/**
 * MINKART - Client-Side Interactive Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Toggle
    const menuToggleBtn = document.querySelector('.mobile-menu-toggle');
    const navLinksMenu = document.querySelector('.nav-links');

    if (menuToggleBtn && navLinksMenu) {
        menuToggleBtn.addEventListener('click', () => {
            navLinksMenu.classList.toggle('active');
        });
    }

    // 2. SVG Image Fallback Handler for missing external images
    const allImages = document.querySelectorAll('img');
    allImages.forEach(img => {
        img.addEventListener('error', function () {
            // Generate clean placeholder SVG
            const altText = this.getAttribute('alt') || 'Product Image';
            const encodedText = encodeURIComponent(altText.substring(0, 25));
            this.src = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><rect width="100%" height="100%" fill="%23f1f5f9"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="16" font-weight="600" fill="%2364748b">${encodedText}</text></svg>`;
        });
    });

    // 3. AJAX Add to Cart Handler
    const ajaxCartForms = document.querySelectorAll('.ajax-add-to-cart');
    ajaxCartForms.forEach(form => {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const actionUrl = this.getAttribute('action');
            const formData = new FormData(this);

            try {
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    showToast(data.message || 'Added to cart!', 'success');
                    // Update cart badge in header
                    const cartBadge = document.querySelector('.cart-badge');
                    if (cartBadge) {
                        cartBadge.textContent = data.cart_count;
                        cartBadge.style.display = 'flex';
                    }
                } else {
                    showToast(data.message || 'Failed to add item.', 'error');
                }
            } catch (err) {
                // Fallback to standard form submit if JS fetch fails
                this.submit();
            }
        });
    });

    // 4. Quantity Input Controls (Plus / Minus buttons)
    const qtyControls = document.querySelectorAll('.qty-control');
    qtyControls.forEach(ctrl => {
        const minusBtn = ctrl.querySelector('.btn-minus');
        const plusBtn = ctrl.querySelector('.btn-plus');
        const input = ctrl.querySelector('.qty-input');

        if (minusBtn && plusBtn && input) {
            minusBtn.addEventListener('click', () => {
                let current = parseInt(input.value) || 1;
                if (current > 1) {
                    input.value = current - 1;
                }
            });

            plusBtn.addEventListener('click', () => {
                let current = parseInt(input.value) || 1;
                let max = parseInt(input.getAttribute('max')) || 99;
                if (current < max) {
                    input.value = current + 1;
                } else {
                    showToast(`Maximum available stock reached (${max}).`, 'warning');
                }
            });
        }
    });

    // 5. Toast Notification Function
    window.showToast = function (message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<span>${message}</span>`;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    };
});
