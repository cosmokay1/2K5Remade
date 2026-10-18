/* Branding for the custom MNF/TNF variations. Layout, data and animation
 * remain the original NFL2K5-PC NBC SNF implementation. */
(function () {
  'use strict';
  var short = document.body.dataset.networkVariation;
  var config = short === 'MNF'
    ? { folder:'ESPN_MNF', night:'MONDAY NIGHT', name:'ESPN' }
    : { folder:'Prime_TNF', night:'THURSDAY NIGHT', name:'Prime Video' };
  var selector = '.nbc-brand,.peacock-user,.snf-wordmark,.pg-peacock,.pg-snf';
  function brand(node) {
    if (node.nodeType === 3) {
      if (node.nodeValue.trim() === 'SNF') node.nodeValue = short;
      else if (node.nodeValue.trim() === 'SUNDAY NIGHT') node.nodeValue = config.night;
      return;
    }
    if (node.nodeType !== 1) return;
    var images = node.matches(selector) ? [node] : node.querySelectorAll(selector);
    Array.from(images).forEach(function (img) {
      img.src = '../' + config.folder + '/brand.svg';
      img.alt = config.name;
    });
    var walk = document.createTreeWalker(node, NodeFilter.SHOW_TEXT), text;
    while ((text = walk.nextNode())) brand(text);
  }
  brand(document.body);
  // New broadcast inserts can contain fresh branding nodes. Observe additions
  // only; never rescan the screen on each clock tick or observe our own attrs.
  new MutationObserver(function (records) {
    records.forEach(function (record) { record.addedNodes.forEach(brand); });
  }).observe(document.body, {childList:true, subtree:true});
})();
