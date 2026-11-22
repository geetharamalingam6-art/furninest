import { Minus, Plus, RefreshCw, ShoppingBag, Trash2, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import useStore from '../hooks/useStore'
import { getProductImage } from '../data/furnitureImagery'

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export default function BagDrawer() {
  const {
    items,
    itemCount,
    subtotal,
    bagOpen,
    cartError,
    cartLoading,
    closeBag,
    retryCart,
    updateQuantity,
    removeItem,
  } = useStore()

  if (!bagOpen) return null

  return (
    <div className="drawer-backdrop" onMouseDown={closeBag}>
      <aside
        className="bag-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="bag-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="drawer-heading">
          <div>
            <span className="eyebrow">YOUR SELECTION</span>
            <h2 id="bag-title">Shopping bag <span>({itemCount})</span></h2>
          </div>
          <button className="icon-button" onClick={closeBag} aria-label="Close bag">
            <X size={19} />
          </button>
        </div>

        {cartLoading ? (
          <div className="bag-empty"><p>Loading your bag…</p></div>
        ) : cartError && items.length === 0 ? (
          <div className="bag-empty">
            <p>{cartError}</p>
            <button className="button button--outline" onClick={retryCart}><RefreshCw size={15} /> Try again</button>
          </div>
        ) : items.length === 0 ? (
          <div className="bag-empty">
            <ShoppingBag size={28} strokeWidth={1.4} />
            <p>Your bag is waiting for something lovely.</p>
            <button className="button button--dark" onClick={closeBag}>Explore the collection</button>
          </div>
        ) : (
          <>
            <div className="bag-items">
              {items.map((item) => {
                const { product, quantity } = item
                const image = getProductImage(product).src
                return (
                <article className="bag-item" key={item.id}>
                  <div className="bag-item-image">
                    <img src={image} alt="" />
                  </div>
                  <div className="bag-item-info">
                    <h3>{product.name}</h3>
                    <p>{money.format(Number(product.current_price ?? product.price))}</p>
                    <div className="quantity-control">
                      <button
                        type="button"
                        aria-label={`Decrease ${product.name} quantity`}
                        onClick={() => updateQuantity(item.id, quantity - 1)}
                      >
                        <Minus size={13} />
                      </button>
                      <span>{quantity}</span>
                      <button
                        type="button"
                        aria-label={`Increase ${product.name} quantity`}
                        disabled={quantity >= product.stock_quantity}
                        onClick={() => updateQuantity(item.id, quantity + 1)}
                      >
                        <Plus size={13} />
                      </button>
                    </div>
                  </div>
                  <button
                    className="icon-button remove-item"
                    type="button"
                    aria-label={`Remove ${product.name}`}
                    onClick={() => removeItem(item.id)}
                  >
                    <Trash2 size={16} />
                  </button>
                </article>
                )
              })}
            </div>
            {cartError && <p className="form-feedback form-feedback--error" role="alert">{cartError}</p>}
            <div className="bag-summary">
              <div><span>Subtotal</span><strong>{money.format(subtotal)}</strong></div>
              <p>Shipping and taxes are calculated at checkout.</p>
              <Link className="button button--dark" to="/checkout" onClick={closeBag}>
                Continue to checkout
              </Link>
            </div>
          </>
        )}
      </aside>
    </div>
  )
}
