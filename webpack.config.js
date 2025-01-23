const path = require("path");

module.exports = {
  entry: "./src/index.js", // Main JavaScript file
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "bundle.js",
  },
  mode: "production", // Set for optimized builds
  module: {
    rules: [
      {
        test: /\.css$/i, // CSS loader
        use: ["style-loader", "css-loader"],
      },
      {
        test: /\.(png|jpg|jpeg|gif|svg)$/i, // Image loader
        type: "asset/resource",
      },
    ],
  },
};
