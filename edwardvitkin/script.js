document.addEventListener('DOMContentLoaded', () => {
    // Entrance animation
    const card = document.getElementById('main-card');
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        card.style.transition = 'opacity 0.8s ease, transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
    }, 100);

    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');

            // Deactivate all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => {
                c.classList.remove('active');
                c.style.animation = 'none';
            });

            // Activate clicked
            btn.classList.add('active');
            const target = document.getElementById(`tab-${targetTab}`);
            target.classList.add('active');

            // Re-trigger animation
            void target.offsetWidth;
            target.style.animation = 'fadeIn 0.3s ease';
        });
    });

    // Parallax on avatar
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const avatar = document.querySelector('.profile-avatar');
        if (avatar) {
            const moveX = (x - rect.width / 2) / 25;
            const moveY = (y - rect.height / 2) / 25;
            avatar.style.transform = `translate(${moveX}px, ${moveY}px)`;
            avatar.style.transition = 'transform 0.1s ease';
        }
    });

    card.addEventListener('mouseleave', () => {
        const avatar = document.querySelector('.profile-avatar');
        if (avatar) {
            avatar.style.transform = 'translate(0px, 0px)';
            avatar.style.transition = 'transform 0.5s ease';
        }
    });
});
