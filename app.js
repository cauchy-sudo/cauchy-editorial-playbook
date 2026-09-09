const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.tab-panel');
const copyButtons = document.querySelectorAll('.copy-prompt');

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    const target = tab.dataset.tab;
    tabs.forEach((item) => item.classList.toggle('active', item === tab));
    panels.forEach((panel) => panel.classList.toggle('active-panel', panel.id === target));
    window.scrollTo({ top: document.querySelector('.tabbar').offsetTop - 12, behavior: 'smooth' });
  });
});

document.querySelectorAll('.role-card').forEach((card) => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.role-card').forEach((item) => item.classList.toggle('selected', item === card));
    const target = document.querySelector(`.tab[data-tab="${card.dataset.role}"]`);
    if (target) target.click();
  });
});

const formatDate = (date) => date.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
const parseDate = (value) => value ? new Date(`${value}T12:00:00`) : null;
const addDays = (date, days) => { const result = new Date(date); result.setDate(result.getDate() + days); return result; };
const addMonths = (date, months) => { const result = new Date(date); const day = result.getDate(); result.setMonth(result.getMonth() + months); if (result.getDate() !== day) result.setDate(0); return result; };

const reviewDate = document.querySelector('#reviewDate');
const reminderDate = document.querySelector('#reminderDate');
const replaceDate = document.querySelector('#replaceDate');
reviewDate.addEventListener('input', () => {
  const date = parseDate(reviewDate.value);
  reminderDate.textContent = date ? formatDate(addDays(date, 14)) : '—';
  replaceDate.textContent = date ? formatDate(addMonths(date, 1)) : '—';
});

const submitDate = document.querySelector('#submitDate');
const acceptedDate = document.querySelector('#acceptedDate');
const acceptedStatus = document.querySelector('#acceptedStatus');
submitDate.addEventListener('input', () => {
  const date = parseDate(submitDate.value);
  acceptedDate.textContent = date ? formatDate(addMonths(date, 2)) : '—';
  acceptedStatus.textContent = date ? 'Belum boleh accepted sebelum tanggal minimum' : 'Masukkan tanggal';
  acceptedStatus.style.color = date ? '#b56a20' : '';
});

copyButtons.forEach((button) => {
  button.addEventListener('click', async () => {
    const code = button.closest('.prompt-card')?.querySelector('code');
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code.innerText);
      const original = button.textContent;
      button.textContent = 'Tersalin';
      setTimeout(() => { button.textContent = original; }, 1500);
    } catch {
      button.textContent = 'Salin manual';
    }
  });
});
