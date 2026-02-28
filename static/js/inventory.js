// simple UI helpers: search, view toggle, image preview
function filterProducts(){
  const q = document.getElementById('searchBox')?.value?.toLowerCase() || '';
  document.querySelectorAll('.product-card, .product-row').forEach(el=>{
    const name = (el.getAttribute('data-name') || '').toLowerCase();
    el.style.display = name.includes(q) ? '' : 'none';
  });
}

function toggleView(view){
  const cards = document.querySelectorAll('[data-ui="cards-area"]');
  const table = document.querySelectorAll('[data-ui="table-area"]');
  if(view==='table'){
    cards.forEach(e=>e.classList.add('hidden'));
    table.forEach(e=>e.classList.remove('hidden'));
  } else {
    table.forEach(e=>e.classList.add('hidden'));
    cards.forEach(e=>e.classList.remove('hidden'));
  }
}

// Mobile sidebar toggle
document.getElementById('sidebarToggle')?.addEventListener('click', ()=>{
  const sb = document.getElementById('sidebar');
  sb.classList.toggle('open');
});

// preview image on product form
function previewImage(input){
  if(!input.files || !input.files[0]) return;
  const file = input.files[0];
  const img = document.getElementById('imgPreview');
  if(!img) return;
  img.src = URL.createObjectURL(file);
  img.classList.remove('hidden');
}
