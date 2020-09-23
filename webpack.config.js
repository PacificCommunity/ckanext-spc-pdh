var webpack = require("webpack");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const HtmlWebpackPlugin = require("html-webpack-plugin");

const path = require("path");

const sveltePath = path.resolve("node_modules", "svelte");

const mode = process.env.NODE_ENV || "production";
const prod = mode === "production";

module.exports = {
  entry: {
    widgets: ["./widgets/main.js"],
  },
  output: {
    path: path.resolve("dist"),
    filename: "widgets.js",
  },
  resolve: {
    alias: {
      svelte: path.resolve("node_modules", "svelte"),
    },
    extensions: [".mjs", ".js", ".svelte"],
    mainFields: ["svelte", "browser", "module", "main"],
  },
  module: {
    rules: [
      // Rules are chained bottom to top. Babel rule must probably be one of
      // the last of the chain, so it must come first in the array.
      {
        test: /\.(?:svelte|m?js)$/,
        // Svelte internals, under node_modules MUST be included.
        //
        // Babel 7 ignores node_modules automatically, but not if they're
        // explicitely included.
        // see: https://github.com/babel/babel-loader/issues/171#issuecomment-486380160
        //
        include: [path.resolve("widgets"), path.dirname(sveltePath)],
        use: {
          loader: "babel-loader",
          options: {
            presets: [
              [
                "@babel/preset-env",
                {
                  targets: "ie >= 9",
                  corejs: 3,
                  useBuiltIns: "entry",
                },
              ],
            ],
          },
        },
      },
      {
        test: /\.svelte$/,
        use: {
          loader: "svelte-loader",
          options: {
            emitCss: true,
            hotReload: true,
          },
        },
      },
      {
        test: /\.css$/,
        use: [
          /**
           * MiniCssExtractPlugin doesn't support HMR.
           * For developing, use 'style-loader' instead.
           * */
          prod ? MiniCssExtractPlugin.loader : "style-loader",
          "css-loader",
        ],
      },
      {
        test: /\.less$/,
        use: [
          prod ? MiniCssExtractPlugin.loader : "style-loader",
          "css-loader",
          "less-loader",
        ],
      },
    ],
  },
  mode,
  plugins: [
    new MiniCssExtractPlugin({
      filename: "[name].css",
    }),
    new HtmlWebpackPlugin({ template: "widgets/index.html" }),
    new webpack.ProvidePlugin({
      Promise: "es6-promise", // Thanks Aaron (https://gist.github.com/Couto/b29676dd1ab8714a818f#gistcomment-1584602)
    }),
  ],
  devtool: prod ? false : "source-map",
};
