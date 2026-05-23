document.addEventListener('DOMContentLoaded', () => {
    // GSAP Animations
    gsap.registerPlugin(ScrollTrigger);

    gsap.from('.reveal-text', {
        duration: 1.2,
        y: 60,
        opacity: 0,
        ease: 'power4.out'
    });

    gsap.from('.fade-in', {
        duration: 1,
        opacity: 0,
        y: 20,
        stagger: 0.2,
        delay: 0.5,
        ease: 'power2.out'
    });

    gsap.from('.card', {
        scrollTrigger: {
            trigger: '#about',
            start: 'top 80%'
        },
        duration: 0.8,
        y: 40,
        opacity: 0,
        stagger: 0.2,
        ease: 'power3.out'
    });

    // Builder Logic (Drag and Drop)
    const blocks = document.querySelectorAll('.block');
    const zones = document.querySelectorAll('.drop-zone');
    const simulateBtn = document.getElementById('simulate-btn');

    blocks.forEach(block => {
        block.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', block.innerText);
            e.dataTransfer.setData('type', block.dataset.type);
            block.style.opacity = '0.5';
        });

        block.addEventListener('dragend', () => {
            block.style.opacity = '1';
        });
    });

    zones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('active');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('active');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('active');
            const data = e.dataTransfer.getData('text/plain');
            zone.innerHTML = `<span>${data}</span>`;
            zone.dataset.filled = 'true';
        });
    });

    // Mock Simulation Logic
    simulateBtn.addEventListener('click', () => {
        const filledZones = Array.from(zones).filter(z => z.dataset.filled === 'true').length;
        
        if (filledZones < 3) {
            alert('Please assemble all 3 modules before running the simulation.');
            return;
        }

        simulateBtn.innerText = 'Analyzing Flux...';
        simulateBtn.disabled = true;

        setTimeout(() => {
            const yieldFill = document.querySelector('.stat:nth-child(2) .fill');
            const efficiencyFill = document.querySelector('.stat:nth-child(3) .fill');
            const yieldValue = document.querySelector('.stat:nth-child(2) .value');
            const efficiencyValue = document.querySelector('.stat:nth-child(3) .value');

            // Deterministic results based on inputs
            const combination = Array.from(zones).map(z => z.innerText.trim()).join('|');
            let hash = 0;
            for (let i = 0; i < combination.length; i++) {
                hash = ((hash << 5) - hash) + combination.charCodeAt(i);
                hash |= 0; // Convert to 32bit integer
            }
            const pseudoRandom = Math.abs(hash) / 2147483647;
            
            const targetYield = (pseudoRandom * 40 + 60).toFixed(2);
            const targetEfficiency = (pseudoRandom * 20 + 75).toFixed(0);

            yieldFill.style.width = `${targetYield}%`;
            efficiencyFill.style.width = `${targetEfficiency}%`;
            
            yieldValue.innerText = `${targetYield} g/L`;
            efficiencyValue.innerText = `${targetEfficiency}%`;

            simulateBtn.innerText = 'Run FBA Simulation';
            simulateBtn.disabled = false;
        }, 2000);
    });

    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        const navbar = document.getElementById('navbar');
        if (window.scrollY > 50) {
            navbar.style.padding = '1rem 4rem';
            navbar.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
        } else {
            navbar.style.padding = '1.5rem 4rem';
            navbar.style.boxShadow = 'none';
        }
    });
});
