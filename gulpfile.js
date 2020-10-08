const { watch, src, dest } = require("gulp");
const sourcemaps = require("gulp-sourcemaps");
const if_ = require("gulp-if");
const less = require("gulp-less");
const touch = require("gulp-touch-cmd");
const isDev = !!process.env.DEBUG;

const root = __dirname + "/ckanext/spc/";
const lessPath = root + "theme/public/base/less";
const publicPath = root + "fanstatic/styles";

const build = () =>
  src(`${lessPath}/spc.less`)
    .pipe(if_(isDev, sourcemaps.init()))
    .pipe(less())
    .pipe(if_(isDev, sourcemaps.write()))
    .pipe(dest(publicPath))
    .pipe(touch());

const observeChanges = () =>
  watch(lessPath + "/*.less", { ignoreInitial: false }, build);

exports.default = observeChanges;
exports.watch = observeChanges;
exports.build = build;
