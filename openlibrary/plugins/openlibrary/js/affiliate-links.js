import { buildPartialsUrl } from './utils'

/**
 * Adds functionality to fetch affiliate links asynchronously.
 *
 * Fetches and attaches partials to DOM iff any of the given affiliate link
 * sections contain a loading indicator. Uses IntersectionObserver to delay
 * fetching until the section is visible.
 *
 * @param {NodeList<HTMLElement>} affiliateLinksSections Collection of each affiliate links section that is on the page
 */
export function initAffiliateLinks(affiliateLinksSections) {
    if (!affiliateLinksSections.length) return

    const intersectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Unregister intersection listener
                intersectionObserver.unobserve(entry.target)

                const section = entry.target
                const loadingIndicator = section.querySelector('.loadingIndicator')

                if (loadingIndicator) {
                    loadingIndicator.classList.remove('hidden')

                    const title = section.dataset.title
                    const opts = JSON.parse(section.dataset.opts)
                    const data = {args: [title, opts]}

                    getPartials(data, section)
                }
            }
        })
    }, {
        root: null,
        rootMargin: '200px',
        threshold: 0
    })

    affiliateLinksSections.forEach(section => intersectionObserver.observe(section))
}

/**
 * Fetches rendered affiliate links template using the given arguments.
 *
 * @param {object} data Contains array of positional arguments for the template
 * @param {HTMLElement} section The specific section to update
 * @returns {Promise}
 */
async function getPartials(data, section) {
    const dataString = JSON.stringify(data)
    const loadingIndicator = section.querySelector('.loadingIndicator')

    return fetch(buildPartialsUrl('AffiliateLinks', {data: dataString}))
        .then((resp) => {
            if (resp.status !== 200) {
                throw new Error(`Failed to fetch partials. Status code: ${resp.status}`)
            }
            return resp.json()
        })
        .then((respData) => {
            // Swap the loading spinner with our new partial content.
            const template = document.createElement('template')
            template.innerHTML = respData.partials
            const newContent = template.content.querySelector('.affiliate-links-section')

            // The partial usually contains the wrapper span, so we just grab its
            // children and drop them into the current section. This keeps our
            // 'section' reference valid for retries and avoids double-nesting.
            if (newContent) {
                section.replaceChildren(...Array.from(newContent.childNodes))
            } else {
                section.replaceChildren(...Array.from(template.content.childNodes))
            }
        })
        .catch((err) => {
            // eslint-disable-next-line no-console
            console.error('Error fetching affiliate links:', err)
            if (loadingIndicator) {
                loadingIndicator.classList.add('hidden')
            }

            const existingRetryAffordance = section.querySelector('.affiliate-links-section__retry')
            if (existingRetryAffordance) {
                existingRetryAffordance.classList.remove('hidden')
            } else {
                section.insertAdjacentHTML('afterbegin', renderRetryLink())
                const retryAffordance = section.querySelector('.affiliate-links-section__retry')
                retryAffordance.addEventListener('click', (e) => {
                    e.preventDefault()
                    retryAffordance.classList.add('hidden')
                    if (loadingIndicator) {
                        loadingIndicator.classList.remove('hidden')
                    }
                    getPartials(data, section)
                })
            }
        })
}

/**
 * Returns HTML string with error message and retry link.
 *
 * @returns {string} HTML for a retry link.
 */
function renderRetryLink() {
    return '<span class="affiliate-links-section__retry">Failed to fetch affiliate links. <a href="javascript:;">Retry?</a></span>'
}
