'use strict';
const grid = document.querySelector('#paper-grid');
const search = document.querySelector('#paper-search');
const journal = document.querySelector('#journal-filter');
const topic = document.querySelector('#topic-filter');
const access = document.querySelector('#access-filter');
const count = document.querySelector('#result-count');
const dialog = document.querySelector('#preview-dialog');
const escapeHtml = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let papers = [];
let lastPreviewButton = null;

function renderCard(p) {
  const e = escapeHtml;
  const pdfUrl = p.pdf ? `${p.pdf}#page=${p.page}` : p.openUrl;
  const preview = p.preview
    ? `<button type="button" class="paper-preview" data-preview="${p.id}" aria-label="Perbesar pratinjau ${e(p.title)}"><img src="${p.preview}" loading="lazy" alt="Cuplikan ${e(p.figure)} pada halaman ${p.page}, ${e(p.title)}"><span>Lihat halaman & caption ↗</span></button>`
    : `<div class="paper-placeholder"><b>${String(p.number).padStart(2, '0')}</b><span>${p.topic === 'Bacaan pendamping' ? 'Bacaan pendamping · tanpa contoh figure' : 'Baca visualisasi pada sumber resmi'}</span></div>`;
  return `<article class="paper-card" id="${p.id}">${preview}<div class="paper-content"><div class="paper-meta"><span>${e(p.journal)}</span><span>· ${p.year}</span></div><span class="paper-topic">${e(p.topic)}</span><h2>${e(p.title)}</h2><p class="paper-authors">${e(p.authors)}</p><p class="paper-figure">${e(p.figure)}${p.page ? ` · halaman PDF ${p.page}` : ''}</p><p class="paper-lesson">${e(p.lesson)}</p><div class="review-question"><strong>PERTANYAAN UNTUK REVIEWER</strong>${e(p.question)}</div><div class="paper-actions"><a href="${e(pdfUrl)}" target="_blank" rel="noopener">${p.pdf ? 'Buka PDF' : 'Baca sumber'} ↗</a><a href="${e(p.sourceUrl)}" target="_blank" rel="noopener">DOI / penerbit ↗</a></div><details><summary>Versi, sumber & atribusi</summary><p>${e(p.note)}</p><p>${e(p.authors)} · ${e(p.journal)} (${p.year}).<br>DOI: ${e(p.doi)}</p>${p.license ? `<p>PDF asli tanpa perubahan. Pratinjau satu halaman dirasterisasi dan diperkecil. Lisensi: <a href="${p.licenseUrl}" target="_blank" rel="noopener">${e(p.license)}</a>. Kredit pihak ketiga tetap berlaku.</p>` : '<p>PDF dan figure tidak disalin ke repositori. Gunakan sumber resmi untuk akses dan ketentuan pemakaian.</p>'}</details></div></article>`;
}

function filter() {
  const q = search.value.toLocaleLowerCase('id');
  let visible = 0;
  papers.forEach(p => {
    const text = [p.title,p.authors,p.journal,p.publisher,p.topic,p.lesson,p.question,p.figure].join(' ').toLocaleLowerCase('id');
    const show = text.includes(q) && (!journal.value || journal.value === p.journal) && (!topic.value || topic.value === p.topic) && (!access.value || (access.value === 'local' ? !!p.pdf : !p.pdf));
    document.getElementById(p.id).hidden = !show;
    if (show) visible++;
  });
  count.textContent = `${visible} dari ${papers.length} paper · ${papers.filter(p => p.pdf).length} PDF tersimpan di GitHub`;
  document.querySelector('#empty-state').hidden = visible > 0;
}

function resetFilters() {
  search.value = journal.value = topic.value = access.value = '';
  filter();
}

function followHash() {
  const id = location.hash.slice(1);
  if (papers.some(p => p.id === id)) {
    resetFilters();
    document.getElementById(id).scrollIntoView({behavior:'smooth',block:'start'});
  }
}

async function init() {
  try {
    const response = await fetch('visualisasi-data.json');
    if (!response.ok) throw new Error('Koleksi tidak dapat dimuat');
    papers = await response.json();
    grid.innerHTML = papers.map(renderCard).join('');
    for (const [select,key] of [[journal,'journal'],[topic,'topic']]) {
      [...new Set(papers.map(p => p[key]))].sort().forEach(value => select.add(new Option(value,value)));
    }
    filter();
    followHash();
  } catch {
    count.textContent = 'Koleksi belum termuat. Muat ulang halaman atau buka catatan sumber di bawah.';
    grid.innerHTML = '<p class="panel"><a href="SOURCES-VISUALISASI.md">Buka daftar sumber dan tautan paper</a></p>';
  }
}

search.addEventListener('input',filter);
[journal,topic,access].forEach(select => select.addEventListener('change',filter));
document.querySelector('#reset-filters').addEventListener('click',resetFilters);
window.addEventListener('hashchange',followHash);
grid.addEventListener('click',event => {
  const button = event.target.closest('[data-preview]');
  if (!button) return;
  const p = papers.find(p => p.id === button.dataset.preview);
  lastPreviewButton = button;
  document.querySelector('#preview-title').textContent = p.title;
  document.querySelector('#preview-credit').textContent = `${p.authors} · ${p.journal} (${p.year}) · ${p.figure} · halaman PDF ${p.page} · ${p.license}`;
  const image = document.querySelector('#preview-image');
  image.src = p.pageImage;
  image.alt = `Halaman ${p.page} dari ${p.title}, menampilkan ${p.figure}`;
  document.querySelector('#preview-pdf').href = `${p.pdf}#page=${p.page}`;
  dialog.showModal();
});
document.querySelector('#close-preview').addEventListener('click',() => dialog.close());
dialog.addEventListener('close',() => lastPreviewButton?.focus());
dialog.addEventListener('click',event => { if (event.target === dialog) { const box = dialog.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close(); } });
init();
