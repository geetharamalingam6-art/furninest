import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, Search, Send } from 'lucide-react'
import usePageMetadata from '../hooks/usePageMetadata'
import api from '../services/api'

const faqGroups = [
  {
    id: 'orders',
    title: 'Orders and Shopping',
    questions: [
      ['How can I place an order?', 'Add the pieces you like to your bag, review your selections, and continue to checkout. The available checkout options will be shown before you place an order.'],
      ['Can I modify my order after placing it?', 'Order changes depend on processing status. Contact us through the contact form as soon as possible; a change is not confirmed until our team replies.'],
      ['How can I track my order?', 'When order tracking is available, sign in and open My Orders to review the latest order information.'],
      ['Can I cancel my order?', 'Cancellation terms are being confirmed. Please contact our team with your order number and we will check what options are available.'],
    ],
  },
  {
    id: 'shipping',
    title: 'Shipping and Delivery',
    questions: [
      ['What are the delivery charges?', 'Delivery charges and service areas have not yet been confirmed. Please review the amount shown at checkout before placing an order.'],
      ['How long does delivery take?', 'Delivery estimates are being confirmed and may vary by item and destination. Any available estimate will be shown during checkout or shared with your order.'],
      ['Do you offer delivery across India?', 'Delivery coverage is being confirmed. Enter your delivery details at checkout to see whether service is available for your location.'],
      ['Will I receive a delivery notification?', 'Available order updates are shown in your account. Notification methods are being confirmed.'],
    ],
  },
  {
    id: 'payments',
    title: 'Payments',
    questions: [
      ['What payment methods are accepted?', 'Accepted payment methods are being confirmed. The options available for your order will be shown at checkout.'],
      ['Is online payment secure?', 'Payment processing and security details are being confirmed. Review the payment provider and information shown at checkout before entering payment details.'],
      ['Can I pay using UPI, debit cards, or credit cards?', 'Supported payment methods may vary. Please check the options presented at checkout; availability is being confirmed.'],
      ['Will I receive an order confirmation?', 'After an order is successfully placed, check the confirmation shown in checkout and the order information in your account. Email notification availability is being confirmed.'],
    ],
  },
  {
    id: 'returns',
    title: 'Returns and Refunds',
    questions: [
      ['What is your return policy?', 'Return terms have not yet been confirmed. Please contact our team before ordering if you need clarification about a particular item.'],
      ['How can I request a return?', 'The return process is being confirmed. Contact our team with your order details and we will advise on the available next steps.'],
      ['How long does a refund take?', 'Refund timing depends on the confirmed policy and payment provider. Timing information is being confirmed.'],
      ['What should I do if my product arrives damaged?', 'Please contact our team with your order number and clear photos of the item and packaging so we can review the issue. Resolution terms are being confirmed.'],
    ],
  },
  {
    id: 'products',
    title: 'Products and Furniture',
    questions: [
      ['How do I choose the right furniture size?', 'Measure the room, doorways, and walking paths before choosing. Product pages include dimensions when the information is available.'],
      ['Are product dimensions available?', 'Dimensions are listed on product pages when supplied for that item. Contact us if a detail you need is missing.'],
      ['How should I maintain my furniture?', 'Care requirements vary by material. Follow the care details provided with the product and contact us if you need item-specific guidance.'],
      ['Are product colors exactly as shown in the images?', 'Color appearance can vary with screens, lighting, and materials. Images are intended as a guide; contact us if you need additional details before ordering.'],
    ],
  },
  {
    id: 'account',
    title: 'Account',
    questions: [
      ['How can I create an account?', 'Choose the account icon and select Register. Enter your details to create an account.'],
      ['How can I reset my password?', 'Use the Forgot password link on the sign-in page and follow the instructions provided.'],
      ['How can I view my previous orders?', 'Sign in and open My Orders to view the orders associated with your account.'],
    ],
  },
  {
    id: 'policy-notices',
    title: 'Policy information',
    questions: [
      ['Where can I read your privacy and terms information?', 'Privacy, terms, warranty, shipping, returns, and payment policies are being confirmed. Please contact us if you need a policy detail before making a purchase.'],
    ],
  },
]

export default function FaqPage() {
  const [search, setSearch] = useState('')
  const [openQuestion, setOpenQuestion] = useState('')
  const [question, setQuestion] = useState('')
  const [assistantAnswer, setAssistantAnswer] = useState('')
  const [assistantError, setAssistantError] = useState('')
  const [asking, setAsking] = useState(false)
  usePageMetadata('FAQ | FurniNest', 'Find answers about FurniNest orders, products, accounts, and support.')

  const visibleGroups = useMemo(() => {
    const query = search.trim().toLowerCase()
    return faqGroups.map((group) => ({
      ...group,
      questions: group.questions.filter(([question, answer]) => (
        !query || `${group.title} ${question} ${answer}`.toLowerCase().includes(query)
      )),
    })).filter((group) => group.questions.length > 0)
  }, [search])

  async function askFurniNest(event) {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (trimmedQuestion.length < 3) {
      setAssistantError('Enter a question with at least 3 characters.')
      return
    }

    setAsking(true)
    setAssistantAnswer('')
    setAssistantError('')
    try {
      const { data } = await api.post(
        '/faq/answer/',
        { question: trimmedQuestion },
        { timeout: 35000 },
      )
      setAssistantAnswer(data.answer)
    } catch (requestError) {
      const detail = requestError.response?.data?.detail
      setAssistantError(
        typeof detail === 'string'
          ? detail
          : 'We could not generate an answer right now. Please try again or contact our team.',
      )
    } finally {
      setAsking(false)
    }
  }

  return (
    <main className="content-page faq-page">
      <div className="page-section">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <Link to="/">Home</Link><span>/</span><span>FAQ</span>
        </nav>
        <header className="page-intro">
          <p className="eyebrow">HELP & INFORMATION</p>
          <h1>How Can We Help?</h1>
          <p>Find answers to common questions about FurniNest.</p>
        </header>
        <label className="faq-search">
          <Search size={17} />
          <span className="visually-hidden">Search for answers</span>
          <input value={search} onChange={(event) => { setSearch(event.target.value); setOpenQuestion('') }} placeholder="Search for answers..." />
        </label>

        <section className="faq-assistant" aria-labelledby="faq-assistant-title">
          <p className="eyebrow">ASK A QUESTION</p>
          <h2 id="faq-assistant-title">Ask FurniNest</h2>
          <p>Get an AI-generated answer about our products and store information.</p>
          <p className="faq-assistant-note">
            Your question is sent to Google Gemini for an answer. Do not include personal, payment, or account details. Answers use verified information but may not cover every detail; contact our team for confirmed policies or order-specific help.
          </p>
          <form className="faq-assistant-form" onSubmit={askFurniNest}>
            <label htmlFor="faq-assistant-question">What would you like to know?</label>
            <textarea
              id="faq-assistant-question"
              required
              minLength={3}
              maxLength={2000}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask about products, orders, or furniture care..."
            />
            <button className="button button--dark" type="submit" disabled={asking}>
              {asking ? 'Getting an answer...' : 'Ask a question'}
              <Send size={15} aria-hidden="true" />
            </button>
          </form>
          {asking && <p className="faq-assistant-status" role="status">Checking your question...</p>}
          {assistantError && <p className="faq-assistant-status faq-assistant-status--error" role="alert">{assistantError}</p>}
          {assistantAnswer && (
            <div className="faq-assistant-answer" role="status" aria-live="polite">
              <h3>Answer</h3>
              <p>{assistantAnswer}</p>
            </div>
          )}
        </section>

        {visibleGroups.length ? (
          <div className="faq-groups">
            {visibleGroups.map((group) => (
              <section className="faq-group" key={group.id} id={group.id}>
                <h2>{group.title}</h2>
                <div className="faq-list">
                  {group.questions.map(([question, answer], index) => {
                    const id = `${group.id}-${index}`
                    const open = openQuestion === id
                    return (
                      <article className={open ? 'faq-item faq-item--open' : 'faq-item'} key={question}>
                        <h3>
                          <button
                            type="button"
                            aria-expanded={open}
                            aria-controls={`${id}-answer`}
                            onClick={() => setOpenQuestion(open ? '' : id)}
                          >
                            <span>{question}</span><ChevronDown size={18} />
                          </button>
                        </h3>
                        <div
                          className={open ? 'faq-answer faq-answer--open' : 'faq-answer'}
                          id={`${id}-answer`}
                          aria-hidden={!open}
                        >
                          <div><p>{answer}</p></div>
                        </div>
                      </article>
                    )
                  })}
                </div>
              </section>
            ))}
          </div>
        ) : (
          <div className="journal-empty">
            <h2>No answers found.</h2>
            <p>Try another search, or contact our team for help.</p>
          </div>
        )}

        <section className="faq-support">
          <p className="eyebrow">HERE TO HELP</p>
          <h2>Still Have Questions?</h2>
          <p>Our team is happy to help you with a product or order question.</p>
          <div>
            <Link className="button button--dark" to="/contact">Contact us</Link>
            <Link className="button button--outline" to="/shop">Explore our store</Link>
          </div>
        </section>
      </div>
    </main>
  )
}
