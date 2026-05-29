(function(){
  // only run on small screens
  function isMobile() { return window.matchMedia('(max-width: 900px)').matches; }
  var lastScroll = 0;
  var ticking = false;
  var header = document.querySelector('header');
  if(!header) return;

  function onScroll() {
    if(!isMobile()) {
      header.classList.remove('header-hidden');
      return;
    }
    var sc = window.scrollY || window.pageYOffset;
    if(!ticking) {
      window.requestAnimationFrame(function(){
        if (sc > lastScroll && sc > 60) {
          header.classList.add('header-hidden');
        } else if (sc < lastScroll) {
          header.classList.remove('header-hidden');
        }
        lastScroll = sc <= 0 ? 0 : sc;
        ticking = false;
      });
      ticking = true;
    }
  }

  // show header on resize if desktop
  window.addEventListener('resize', function(){ if(!isMobile()) header.classList.remove('header-hidden'); });
  window.addEventListener('scroll', onScroll, {passive:true});
  // ensure initial state visible
  header.classList.remove('header-hidden');
})();
