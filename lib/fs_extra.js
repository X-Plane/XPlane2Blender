var path = require('path');
var fs = require('fs');

fs.isDir = function(dir, cb)
{
  fs.stat(dir, function(error, stats) {
    if (error) {
      cb(error);
      return;
    };

    cb(nul, stats.isDirectory());
  });
}

fs.isDirSync = function(dir)
{
  var stats = fs.statSync(dir);

  return stats.isDirectory();
}

fs.readdirRecursiveSync = function(dir, ignore)
{
  if (typeof ignore !== 'object') {
    var ignore = [];
  }

  var files = [];

  var _files = fs.readdirSync(dir);

  _files.forEach(function(file) {
    if (ignore.indexOf(file) >= 0) {
      return;
    }

    var fullPath = path.join(dir, file);

    // recursion
    if (fs.isDirSync(fullPath)) {
      var __files = fs.readdirRecursiveSync(fullPath, ignore);

      __files.forEach(function(_file) {
        files.push(_file);
      });
    }
    else {
      files.push(fullPath);
    }
  });

  return files;
}

module.exports = fs;