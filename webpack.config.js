const path = require('path');

module.exports = {
  entry: './src/index.js', // Entry point for your application
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
  },
  mode: 'development', // Change to 'production' for optimized builds
};
