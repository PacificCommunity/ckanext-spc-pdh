/*
*   MA5 jquery mobile menu
*   v 1.0
*   Copyright (c) 2015 Tomasz Kalinowski
*   http://mobile-menu.ma5.pl
*   GitHub: https://github.com/ma-5/ma5-mobile-menu
*/
(function ($) {
    $('body').append('<div class="ma5-mobile-menu-container"/>');
    $('.ma5-menu-mobile').find('ul').clone().addClass('ma5-menu-panel').appendTo('.ma5-mobile-menu-container').find('ul').remove();
    $('.ma5-toggle-menu').on('click touch', function () { $('html').toggleClass('ma5-menu-active')});
    $('.ma5-btn-enter').on('click touch', function () {
        $('.ma5-menu-panel').removeClass('ma5-active-ul');
        $('.ma5-menu-panel li').removeClass('ma5-active-li');
        var itemPath = $(this).parent().attr('class').replace("li", "ul");
        var itemParent = $(this).parent().attr('class').replace("li", "ul").split('-');
        var spliced = itemParent.splice(-1, 1);
        var itemParent = itemParent.join("-");
        $('.ma5-menu-panel').removeClass('ma5-active-leave ma5-parent-leave ma5-active-enter ma5-parent-enter');
        $('.ma5-menu-panel.' + itemParent).addClass('ma5-parent-enter');
        $('.ma5-menu-panel.' + itemPath).addClass('ma5-active-enter');
    });
    $('.ma5-leave-bar').on('click touch', function () {
        var itemNext = $(this).next().attr('class').replace("li", "ul").split('-');
        var splicedNext = itemNext.splice(-1, 1);
        var splicedNext = itemNext.splice(-1, 1);
        var itemNext = itemNext.join("-");
        var itemPath = $(this).next().attr('class').replace("li", "ul").split('-');
        var spliced = itemPath.splice(-1, 1);
        var itemPath = itemPath.join("-");
        $('.ma5-menu-panel').removeClass('ma5-active-leave ma5-parent-leave ma5-active-enter ma5-parent-enter');
        $('.ma5-menu-panel.' + itemNext).addClass('ma5-parent-leave');
        $('.ma5-menu-panel.' + itemPath).addClass('ma5-active-leave'); 
    });
}(jQuery));
