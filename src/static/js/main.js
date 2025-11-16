// Enhanced JavaScript for Hoosier Hub
document.addEventListener("DOMContentLoaded", () => {
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', e => {
            const targetId = link.getAttribute('href');
            if (targetId !== '#' && targetId.length > 1) {
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Active navigation highlighting
    const normalizePath = (path) => {
        if (!path) return '';
        if (path.length > 1 && path.endsWith('/')) {
            return path.slice(0, -1);
        }
        return path;
    };

    const currentPath = normalizePath(window.location.pathname);

    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        const prefixAttr = link.dataset.activePrefix;
        const targets = [];

        if (prefixAttr) {
            prefixAttr.split(',').forEach(item => {
                const cleaned = normalizePath(item.trim());
                if (cleaned) targets.push(cleaned);
            });
        } else {
            const href = link.getAttribute('href');
            const cleaned = normalizePath(href);
            if (cleaned && cleaned !== '#') {
                targets.push(cleaned);
            }
        }

        const isActive = targets.some(target => {
            if (!target) return false;
            if (target === '/') {
                return currentPath === '/';
            }
            return currentPath === target || currentPath.startsWith(`${target}/`) || currentPath.startsWith(target);
        });

        if (isActive) {
            link.classList.add('active');
            const parentItem = link.closest('.nav-item');
            parentItem?.classList.add('active');
        }
    });

    // Navbar scroll effect
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar-modern');

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.12)';
            navbar.style.padding = '0.75rem 0';
        } else {
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.08)';
            navbar.style.padding = '1rem 0';
        }

        lastScroll = currentScroll;
    });

    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all cards and sections
    document.querySelectorAll('.feature-card, .trend-card, .quote').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // Card hover effects enhancement
    const cards = document.querySelectorAll('.feature-card, .trend-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
        });
    });

    // Button ripple effect
    const buttons = document.querySelectorAll('.btn-primary, .btn-login, .btn-outline-danger');
    buttons.forEach(button => {
        button.addEventListener('click', function (e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');

            this.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Add ripple effect styles
    const style = document.createElement('style');
    style.textContent = `
        .btn {
            position: relative;
            overflow: hidden;
        }
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple-animation 0.6s ease-out;
            pointer-events: none;
        }
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // Parallax effect for hero section
    const hero = document.querySelector('.hero2');
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            if (scrolled < hero.offsetHeight) {
                hero.style.transform = `translateY(${scrolled * 0.5}px)`;
            }
        });
    }

    // Lazy loading for images
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        // Fallback for browsers that don't support lazy loading
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
        document.body.appendChild(script);
    }

    // Console welcome message
    console.log('%c🏛️ Hoosier Hub', 'color: #990000; font-size: 20px; font-weight: bold;');
    console.log('%cWelcome to the Hoosier Hub booking experience!', 'color: #718096; font-size: 12px;');
});

// Add loading state management
window.addEventListener('load', () => {
    document.body.classList.add('loaded');
});

// Error handling for images
document.addEventListener('error', (e) => {
    if (e.target.tagName === 'IMG') {
        e.target.style.display = 'none';
    }
}, true);


document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("assistant-form");
    const input = document.getElementById("assistant-input");
    const chatBox = document.getElementById("assistant-chat");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const query = input.value.trim();
            if (!query) return;
            chatBox.innerHTML += `<p><strong>You:</strong> ${query}</p>`;
            input.value = "";
            const res = await fetch("/assistant/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query }),
            });
            const data = await res.json();
            chatBox.innerHTML += `<p class="text-danger"><strong>AI:</strong> ${data.answer}</p>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("assistant-form");
    const input = document.getElementById("assistant-input");
    const chatBox = document.getElementById("assistant-chat");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const query = input.value.trim();
            if (!query) return;
            chatBox.innerHTML += `<p><strong>You:</strong> ${query}</p>`;
            input.value = "";
            const res = await fetch("/assistant/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query }),
            });
            const data = await res.json();
            chatBox.innerHTML += `<p class="text-danger"><strong>AI:</strong> ${data.answer}</p>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    }
});
// Nova widget toggle + basic chat mock
document.addEventListener("DOMContentLoaded", () => {
    const widget = document.getElementById("nova-widget");
    const toggle = document.getElementById("nova-toggle");
    const closeBtn = document.getElementById("nova-close");
    const chat = document.getElementById("nova-chat");
    const form = document.getElementById("nova-form");
    const input = document.getElementById("nova-input");
    const quickReplies = document.getElementById("nova-quick-replies");

    const defaultQuickReplies = [
        "Show menu",
        "How do I book a resource?",
        "Waitlist help",
        "Contact admin",
    ];

    const addMessage = (text, role = "nova") => {
        if (!chat) return;
        const bubble = document.createElement("div");
        bubble.classList.add("message", role);
        bubble.innerHTML = text;
        chat.appendChild(bubble);
        chat.scrollTop = chat.scrollHeight;
    };

    const addTypingIndicator = () => {
        const indicator = document.createElement("div");
        indicator.classList.add("message", "nova", "typing");
        indicator.innerHTML = "<span></span><span></span><span></span>";
        chat.appendChild(indicator);
        chat.scrollTop = chat.scrollHeight;
        return indicator;
    };

    const renderSuggestions = (suggestions = []) => {
        if (!suggestions.length || !chat) return;
        const wrapper = document.createElement("div");
        wrapper.classList.add("nova-suggestions");
        suggestions.forEach((item) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.classList.add("nova-suggestion-btn");
            btn.innerHTML = `<span>${item.label}</span><small>${item.description}</small>`;
            btn.addEventListener("click", () => {
                window.location.href = item.url;
            });
            wrapper.appendChild(btn);
        });
        chat.appendChild(wrapper);
        chat.scrollTop = chat.scrollHeight;
    };

    const renderQuickReplies = (replies = []) => {
        if (!quickReplies) return;
        quickReplies.innerHTML = "";
        const data = replies.length ? replies : defaultQuickReplies;
        data.forEach((label) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.classList.add("nova-quick-reply");
            btn.textContent = label;
            btn.addEventListener("click", () => {
                input.value = label;
                form.dispatchEvent(new Event("submit"));
            });
            quickReplies.appendChild(btn);
        });
    };

    toggle?.addEventListener("click", () => {
        widget.classList.toggle("collapsed");
    });

    closeBtn?.addEventListener("click", () => {
        widget.classList.add("collapsed");
    });

    form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = input.value.trim();
        if (!msg) return;
        addMessage(msg, "user");
        input.value = "";

        const typing = addTypingIndicator();

        try {
            const res = await fetch("/assistant/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: msg }),
            });

            const data = await res.json();
            typing.remove();
            addMessage(data.answer || "Let me know how I can help!", "nova");

            // If there's a primary_link, render it first as a prominent card
            if (data.primary_link) {
                const primaryWrapper = document.createElement("div");
                primaryWrapper.classList.add("nova-primary-link");
                const primaryBtn = document.createElement("button");
                primaryBtn.type = "button";
                primaryBtn.classList.add("nova-primary-btn");
                primaryBtn.innerHTML = `<strong>${data.primary_link.label}</strong><br><small>${data.primary_link.description || ''}</small>`;
                primaryBtn.addEventListener("click", () => {
                    window.location.href = data.primary_link.url;
                });
                primaryWrapper.appendChild(primaryBtn);
                chat.appendChild(primaryWrapper);
                chat.scrollTop = chat.scrollHeight;
            }

            renderSuggestions(data.suggestions || []);
            renderQuickReplies(data.quick_replies || []);
        } catch (error) {
            typing.remove();
            addMessage("I ran into an issue reaching the assistant service. Please try again.", "nova");
        }
    });

    renderQuickReplies();
});


