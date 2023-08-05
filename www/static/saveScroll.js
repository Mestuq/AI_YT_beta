$(window).on('load', function () 
{
    const storedScrollPosition = localStorage.getItem('saveScroll');
    $(window).scrollTop(storedScrollPosition || 0);
});

function runFunction() 
{
    localStorage.setItem('saveScroll', $(window).scrollTop());
}

const t = setInterval(runFunction, 500);