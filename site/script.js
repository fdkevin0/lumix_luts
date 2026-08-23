(function () {
  'use strict';

  var data = JSON.parse(document.getElementById('luts-data').textContent);
  var grid = document.getElementById('lut-grid');
  var modal = document.getElementById('modal');
  var modalContent = document.getElementById('modal-content');
  var resultCount = document.getElementById('result-count');

  var activeCollection = '';
  var activeStyle = '';
  var activeTags = [];
  var searchText = '';

  function githubRawUrl(relPath) {
    if (!window.REPO_SLUG) return '#' + relPath;
    return 'https://raw.githubusercontent.com/' + window.REPO_SLUG + '/main/' + encodeURI(relPath);
  }

  function renderCards(entries) {
    grid.innerHTML = '';
    entries.forEach(function (e) {
      var card = document.createElement('div');
      card.className = 'card';
      card.dataset.id = e.id;

      var previewHtml = e.preview
        ? '<img src="' + githubRawUrl(e.preview) + '" alt="' + escHtml(e.name) + '">'
        : '<div class="placeholder"></div>';

      var tagsHtml = e.tags.map(function (t) {
        return '<span class="chip">' + escHtml(t) + '</span>';
      }).join('');

      card.innerHTML =
        '<div class="card-preview">' + previewHtml + '</div>' +
        '<div class="card-body">' +
          '<div class="card-title">' + escHtml(e.name) + '</div>' +
          '<div class="card-title-zh">' + escHtml(e.name_zh) + '</div>' +
          '<div class="card-meta">' +
            '<span class="badge badge-style">' + escHtml(e.photo_style) + '</span>' +
            '<span class="card-author">' + escHtml(e.author) + '</span>' +
          '</div>' +
          '<div class="card-tags">' + tagsHtml + '</div>' +
        '</div>';

      card.addEventListener('click', function () { openModal(e); });
      grid.appendChild(card);
    });
    resultCount.textContent = entries.length + ' 个 LUT' + (entries.length !== data.length ? ' (已筛选 / filtered)' : '');
  }

  function openModal(e) {
    var descZh = e.description_zh ? '<p>' + escHtml(e.description_zh) + '</p>' : '';
    var descEn = e.description_en ? '<p lang="en">' + escHtml(e.description_en) + '</p>' : '';

    modalContent.innerHTML =
      '<button class="modal-close" aria-label="Close">&times;</button>' +
      '<h2>' + escHtml(e.name) + '</h2>' +
      '<h3>' + escHtml(e.name_zh) + '</h3>' +
      '<div class="modal-desc">' + descZh + descEn + '</div>' +
      '<a class="download-btn" href="' + githubRawUrl(e.file) + '" download>下载 .cube / Download</a>' +
      '<dl class="modal-info">' +
        '<dt>Author / 作者</dt><dd>' + escHtml(e.author) + '</dd>' +
        '<dt>Collection / 合集</dt><dd>' + escHtml(e.collection_en) + ' / ' + escHtml(e.collection) + '</dd>' +
        '<dt>Base Photo Style</dt><dd>' + escHtml(e.photo_style) + '</dd>' +
        '<dt>Tags / 标签</dt><dd>' + e.tags.map(escHtml).join(', ') + '</dd>' +
      '</dl>';

    modalContent.querySelector('.modal-close').addEventListener('click', closeModal);
    modal.classList.add('open');
  }

  function closeModal() {
    modal.classList.remove('open');
  }

  modal.addEventListener('click', function (ev) {
    if (ev.target === modal) closeModal();
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') closeModal();
  });

  function filter() {
    var q = searchText.toLowerCase();
    var results = data.filter(function (e) {
      if (activeCollection && e.collection !== activeCollection) return false;
      if (activeStyle && e.photo_style !== activeStyle) return false;
      if (activeTags.length && !activeTags.some(function (t) { return e.tags.indexOf(t) >= 0; })) return false;
      if (q) {
        var hay = (e.name + ' ' + e.name_zh + ' ' + e.author + ' ' + e.tags.join(' ') + ' ' + e.description_zh + ' ' + e.description_en).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
    renderCards(results);
  }

  // Collection filter
  var collectionSelect = document.getElementById('collection-filter');
  collectionSelect.addEventListener('change', function () {
    activeCollection = this.value;
    filter();
  });

  // Search
  var searchInput = document.getElementById('search');
  var searchTimer;
  searchInput.addEventListener('input', function () {
    clearTimeout(searchTimer);
    var val = this.value;
    searchTimer = setTimeout(function () {
      searchText = val;
      filter();
    }, 250);
  });

  // Style chips
  document.getElementById('style-chips').addEventListener('click', function (ev) {
    var chip = ev.target.closest('.chip');
    if (!chip) return;
    var style = chip.dataset.style;
    if (activeStyle === style) {
      activeStyle = '';
      chip.classList.remove('active');
    } else {
      document.querySelectorAll('#style-chips .chip').forEach(function (c) { c.classList.remove('active'); });
      activeStyle = style;
      chip.classList.add('active');
    }
    filter();
  });

  // Tag chips
  document.getElementById('tag-chips').addEventListener('click', function (ev) {
    var chip = ev.target.closest('.chip');
    if (!chip) return;
    var tag = chip.dataset.tag;
    var idx = activeTags.indexOf(tag);
    if (idx >= 0) {
      activeTags.splice(idx, 1);
      chip.classList.remove('active');
    } else {
      activeTags.push(tag);
      chip.classList.add('active');
    }
    filter();
  });

  // Initial render
  renderCards(data);
})();

function escHtml(s) {
  var div = document.createElement('div');
  div.textContent = s || '';
  return div.innerHTML;
}
