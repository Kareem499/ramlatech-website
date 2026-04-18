const nav = document.querySelector('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 30);
});
const burger = document.querySelector('.nav-burger');
const navLinks = document.querySelector('.nav-links');
if (burger) {
  burger.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    const spans = burger.querySelectorAll('span');
    const isOpen = navLinks.classList.contains('open');
    spans[0].style.transform = isOpen ? 'rotate(45deg) translate(5px, 5px)' : '';
    spans[1].style.opacity   = isOpen ? '0' : '1';
    spans[2].style.transform = isOpen ? 'rotate(-45deg) translate(5px, -5px)' : '';
  });
  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => navLinks.classList.remove('open'));
  });
}
const revealEls = document.querySelectorAll('.reveal');
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
  });
}, { threshold: 0.12 });
revealEls.forEach(el => io.observe(el));
const path = window.location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.nav-links a').forEach(a => {
  const href = a.getAttribute('href') || '';
  if (href === path || (path === '' && href === 'index.html')) {
    a.classList.add('active');
  }
});
// Newsletter signup — band + footer
document.querySelectorAll('[data-newsletter]').forEach(form => {
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const email = form.querySelector('input[name="fields[email]"]').value;
    const data = new URLSearchParams({ 'fields[email]': email, 'ml-submit': '1', 'anticsrf': 'true' });
    try {
      await fetch('https://assets.mailerlite.com/jsonp/2267517/forms/184727574659729402/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data,
        mode: 'no-cors'
      });
    } catch(err) {}
    form.style.display = 'none';
    form.nextElementSibling.style.display = 'block';
  });
});
