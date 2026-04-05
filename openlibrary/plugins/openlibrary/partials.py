import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from urllib.parse import parse_qs

import httpx
import web
from pydantic import BaseModel

from infogami.utils.view import render_template
from openlibrary.accounts import get_current_user
from openlibrary.core.helpers import affiliate_id
from openlibrary.core.vendors import (
    get_amazon_metadata_async,
    get_betterworldbooks_metadata_async,
    get_affiliate_stores,
)
from openlibrary.core.fulltext import fulltext_search_async
from openlibrary.core.lending import compose_ia_url, get_available
from openlibrary.i18n import gettext as _
from openlibrary.plugins.openlibrary.lists import get_lists_async, get_user_lists
from openlibrary.plugins.upstream.yearly_reading_goals import get_reading_goals
from openlibrary.plugins.worksearch.code import do_search, work_search
from openlibrary.plugins.worksearch.subjects import (
    date_range_to_publish_year_filter,
    get_subject,
)
from openlibrary.views.loanstats import get_trending_books


class PartialDataHandler(ABC):
    """Base class for partial data handlers.

    Has a single method, `generate`, that is expected to return a
    JSON-serializable dict that contains data necessary to update
    a page.
    """

    @abstractmethod
    def generate(self) -> dict:
        pass

    async def generate_async(self) -> dict:
        """Async version of generate.

        By default, calls the synchronous generate method. Subclasses
        can override this to provide a fully asynchronous implementation.
        """
        return self.generate()


class ReadingGoalProgressPartial(PartialDataHandler):
    """Handler for reading goal progress."""

    def __init__(self, year: int):
        self.year = year

    def generate(self) -> dict:
        year = self.year or datetime.now().year
        goal = get_reading_goals(year=year)
        component = render_template('reading_goals/reading_goal_progress', [goal])

        return {"partials": str(component)}


class MyBooksDropperListsPartial(PartialDataHandler):
    """Handler for the MyBooks dropper list component."""

    def generate(self) -> dict:
        user_lists = get_user_lists(None)

        dropper = render_template("lists/dropper_lists", user_lists)
        list_data = {
            list_data['key']: {
                'members': list_data['list_items'],
                'listName': list_data['name'],
            }
            for list_data in user_lists
        }

        return {
            'dropper': str(dropper),
            'listData': list_data,
        }


class CarouselLoadMoreParams(BaseModel):
    """Parameters for the carousel load-more partial."""

    queryType: str = ""
    q: str = ""
    limit: int = 18
    page: int = 1
    sorts: str = ""
    subject: str = ""
    hasFulltextOnly: bool = False
    key: str = ""
    layout: str | None = None
    published_in: str = ""


class CarouselCardPartial(PartialDataHandler):
    """Handler for carousel "load_more" requests"""

    MAX_VISIBLE_CARDS = 5

    def __init__(self, params: CarouselLoadMoreParams):
        self.params = params

    def generate(self) -> dict:
        p = self.params

        # Do search
        search_results = self._make_book_query(p.queryType, p)

        # Render cards
        cards = []
        for index, work in enumerate(search_results):
            lazy = index > self.MAX_VISIBLE_CARDS
            editions = work.get('editions', {})
            if not editions:
                book = work
            elif isinstance(editions, list):
                book = editions[0]
            else:
                book = editions.get('docs', [None])[0]
            book['authors'] = work.get('authors', [])

            cards.append(
                render_template(
                    "books/custom_carousel_card",
                    web.storage(book),
                    lazy,
                    p.layout,
                    key=p.key,
                )
            )

        return {"partials": [str(template) for template in cards]}

    def _make_book_query(self, query_type: str, params: CarouselLoadMoreParams) -> list:
        if query_type == "SEARCH":
            return self._do_search_query(params)
        if query_type == "BROWSE":
            return self._do_browse_query(params)
        if query_type == "TRENDING":
            return self._do_trends_query(params)
        if query_type == "SUBJECTS":
            return self._do_subjects_query(params)

        raise ValueError("Unknown query type")

    def _do_search_query(self, params: CarouselLoadMoreParams) -> list:
        fields = [
            'key',
            'title',
            'subtitle',
            'author_name',
            'cover_i',
            'ia',
            'availability',
            'id_project_gutenberg',
            'id_project_runeberg',
            'id_librivox',
            'id_standard_ebooks',
            'id_openstax',
            'editions',
        ]
        query_params: dict = {"q": params.q}
        if params.hasFulltextOnly:
            query_params['has_fulltext'] = 'true'

        results = work_search(
            query_params,
            sort=params.sorts or "new",
            fields=','.join(fields),
            limit=params.limit,
            facet=False,
            offset=params.page,
        )
        return results.get("docs", [])

    def _do_browse_query(self, params: CarouselLoadMoreParams) -> list:
        url = compose_ia_url(
            query=params.q,
            limit=params.limit,
            page=params.page,
            subject=params.subject,
            sorts=params.sorts.split(',') if params.sorts else [],
            advanced=True,
            safe_mode=True,
        )
        results = get_available(url=url)
        return results if "error" not in results else []

    def _do_trends_query(self, params: CarouselLoadMoreParams) -> list:
        return get_trending_books(
            minimum=3, limit=params.limit, page=params.page, sort_by_count=False
        )

    def _do_subjects_query(self, params: CarouselLoadMoreParams) -> list:
        publish_year = date_range_to_publish_year_filter(params.published_in)
        subject = get_subject(
            params.q, offset=params.page, limit=params.limit, publish_year=publish_year
        )
        return subject.get("works", [])


class AffiliateLinksPartial(PartialDataHandler):
    """Handler for affiliate links"""

    def __init__(self, data: dict):
        self.data = data

    def generate(self) -> dict:
        args = self.data.get("args", [])

        if len(args) < 2:
            raise ValueError("Unexpected amount of arguments")

        macro = web.template.Template.globals['macros'].AffiliateLinks(args[0], args[1])
        return {"partials": str(macro)}

    async def generate_async(self) -> dict:
        from openlibrary.plugins.openlibrary.code import is_bot

        args = self.data.get("args", [])
        if len(args) < 2:
            raise ValueError("Unexpected amount of arguments")

        title, opts = args[0], args[1]
        prices = opts.get('prices')
        isbn = opts.get('isbn', '')
        asin = opts.get('asin', '')

        bwb_price = amazon_price = None

        # Fetch price data async with a shared client Parallelized
        if not is_bot() and prices and isbn:
            async with httpx.AsyncClient() as client:
                bwb_task = get_betterworldbooks_metadata_async(isbn, client=client)
                amz_task = None
                if asin or isbn:
                    amz_task = get_amazon_metadata_async(
                        isbn, resources='prices', client=client
                    )

                tasks = [bwb_task]
                if amz_task:
                    tasks.append(amz_task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results safely
                bwb_metadata = results[0] if not isinstance(results[0], Exception) else None
                amz_metadata = None
                if amz_task:
                    amz_metadata = results[1] if not isinstance(results[1], Exception) else None

                if bwb_metadata:
                    bwb_price = bwb_metadata.get('price')
                    # BWB often includes a market_price (Amazon); initialize with it as a fallback
                    amazon_price = bwb_metadata.get('market_price')

                # Prefer the more current direct Amazon API price if available
                if amz_metadata and amz_metadata.get('price'):
                    amazon_price = amz_metadata.get('price')

        opts['prepared_stores'] = get_affiliate_stores(
            title,
            {
                'isbn': isbn,
                'asin': asin,
                'bwb_price': bwb_price,
                'amazon_price': amazon_price,
            },
        )
        macro = web.template.Template.globals['macros'].AffiliateLinks(title, opts)
        return {"partials": str(macro)}


class SearchFacetsPartial(PartialDataHandler):
    """Handler for search facets sidebar and "selected facets" affordances."""

    def __init__(self, data: dict, sfw: bool = False):
        self.sfw = sfw
        self.data = data
        user = get_current_user()
        self.show_merge_authors = user and (
            user.is_librarian() or user.is_super_librarian() or user.is_admin()
        )

    def generate(self) -> dict:
        path = self.data.get('path')
        query = self.data.get('query', '')
        parsed_qs = parse_qs(query.replace('?', ''))
        param = self.data.get('param', {})

        sort = None
        search_response = do_search(
            param,
            sort,
            rows=0,
            spellcheck_count=3,
            facet=True,
            request_label='BOOK_SEARCH_FACETS',
            sfw=self.sfw,
        )

        sidebar = render_template(
            'search/work_search_facets',
            param,
            facet_counts=search_response.facet_counts,
            async_load=False,
            path=path,
            query=parsed_qs,
            show_merge_authors=self.show_merge_authors,
        )

        active_facets = render_template(
            'search/work_search_selected_facets',
            param,
            search_response,
            param.get('q', ''),
            path=path,
            query=parsed_qs,
        )

        return {
            "sidebar": str(sidebar),
            "title": active_facets.title,
            "activeFacets": str(active_facets).strip(),
        }


class FullTextSuggestionsPartial(PartialDataHandler):
    """Handler for rendering full-text search suggestions."""

    def __init__(self, query: str):
        self.query = query or ""
        self.has_error: bool = False

    def generate(self) -> dict:
        raise NotImplementedError("Use generate_async instead")

    async def generate_async(self) -> dict:
        query = self.query
        data = await fulltext_search_async(query)
        # Add caching headers only if there were no errors in the search results
        self.has_error = "error" in data
        hits = data.get('hits', [])
        if not hits['hits']:
            macro = '<div></div>'
        else:
            macro = web.template.Template.globals['macros'].FulltextSearchSuggestion(
                query, data
            )
        return {"partials": str(macro)}


class BookPageListsPartial(PartialDataHandler):
    """Handler for rendering the book page "Lists" section"""

    def __init__(self, workId: str, editionId: str):
        self.workId = workId
        self.editionId = editionId

    def generate(self) -> dict:
        raise NotImplementedError("Use generate_async instead")

    async def generate_async(self) -> dict:
        results: dict = {"partials": []}
        keys = [k for k in (self.workId, self.editionId) if k]

        # Do checks and render
        lists = await get_lists_async(keys)
        results["hasLists"] = bool(lists)

        if not lists:
            results["partials"].append(_('This work does not appear on any lists.'))
        else:
            query = "seed_count:[2 TO *] seed:(%s)" % " OR ".join(
                f'"{k}"' for k in keys
            )
            all_url = "/search/lists?q=" + web.urlquote(query) + "&sort=last_modified"
            lists_template = render_template("lists/carousel", lists, all_url)
            results["partials"].append(str(lists_template))

        return results


class LazyCarouselParams(BaseModel):
    """Parameters for the lazy carousel partial."""

    query: str = ""
    title: str | None = None
    sort: str = "new"
    key: str = ""
    limit: int = 20
    search: bool = False
    has_fulltext_only: bool = True
    url: str | None = None
    layout: str = "carousel"
    fallback: str | None = None


class LazyCarouselPartial(PartialDataHandler):
    """Handler for lazily-loaded query carousels."""

    def __init__(self, params: LazyCarouselParams):
        self.params = params

    def generate(self) -> dict:
        macro = web.template.Template.globals['macros'].CacheableMacro(
            "RawQueryCarousel",
            self.params.query,
            lazy=False,
            title=self.params.title,
            sort=self.params.sort,
            key=self.params.key,
            limit=self.params.limit,
            search=self.params.search,
            has_fulltext_only=self.params.has_fulltext_only,
            url=self.params.url,
            layout=self.params.layout,
            fallback=self.params.fallback,
        )
        return {"partials": str(macro)}


def setup():
    pass
