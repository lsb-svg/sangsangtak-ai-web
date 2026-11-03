document.addEventListener('DOMContentLoaded', () => {
  const box = document.getElementById('question-search');
  const rows = [...document.querySelectorAll('[data-question]')];
  const empty = document.getElementById('qa-empty');
  const chips = [...document.querySelectorAll('.cat-chip')];
  let selectedCat = 'all';

  function filter() {
    const term = box ? box.value.trim().toLocaleLowerCase('ko') : '';
    let shown = 0;
    for (const row of rows) {
      const cat = row.dataset.category || '';
      const matchCat = (selectedCat === 'all') || (cat === selectedCat);
      const matchTerm = !term || row.dataset.question.toLocaleLowerCase('ko').includes(term);
      const yes = matchCat && matchTerm;
      row.hidden = !yes;
      if (yes) shown++;
    }
    if (empty) empty.hidden = (shown !== 0);
  }

  if (box) {
    box.addEventListener('input', filter);
  }

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      selectedCat = chip.dataset.cat || 'all';
      filter();
    });
  });
});
