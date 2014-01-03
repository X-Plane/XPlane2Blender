var fs = require('./lib/fs_extra');
var path = require('path');
var ejs = require('ejs');
var markdown = require('marked');
var utils = require('utilities');
var cp = require('child_process');
var st = require('st');
var http = require('http');

task('watch', function() {
    var pagesPath = path.join(__dirname, 'pages');
    utils.file.watch(pagesPath, { includePattern: /(\.md)$/}, function(filePath) {
        jake.Task['compile'].reenable();
        jake.Task['compile'].invoke(filePath);
    });

    utils.file.watch(path.join(__dirname, 'templates'), { includePattern: /(\.ejs)$/}, function(filePath) {
        jake.Task['build'].reenable();
        jake.Task['build'].invoke();
    });
});

task('compile', function(filePath) {
    var htmlTemplatePath = path.join(__dirname, 'templates/layout.html.ejs');
    var htmlTemplate = fs.readFileSync(htmlTemplatePath, { encoding:'utf-8' });

    var pagesPath = path.join(__dirname, 'pages');

    var filePathRelative = path.relative(pagesPath, filePath);
    var fileDir = path.dirname(filePathRelative);
    var filename = path.basename(filePathRelative, '.md');
    var title = filename.replace(/-|_/,' ');

    // create subdirectories
    if (fileDir && fileDir.length > 0) {
        jake.mkdirP(fileDir);
    }

    // markdow to html
    var body = fs.readFileSync(filePath, { encoding: 'utf-8'});
    body = markdown(body, { breaks: false });

    // compile to html
    var html = ejs.render(htmlTemplate, { filename: htmlTemplatePath, title: title, body: body });
    var htmlFilePath = path.join(__dirname, fileDir, filename + '.html');
    fs.writeFileSync(htmlFilePath, html, { encoding: 'utf-8'});

    console.log('compiled ' + path.relative(__dirname, htmlFilePath));
});

task('serve', ['watch'], function(port) {
    if (!port) {
        port = 4000;
    }

    http.createServer(
        st({path: process.cwd(), cache: false})
    ).listen(port);

    console.log('started server on port ' + port);
});

task('build', {async: true}, function(){
    var pageFiles = fs.readdirRecursiveSync('./pages');

    pageFiles.filter(function(filePath) {
       return (path.extname(filePath) !== '.md');
    });

    pageFiles.forEach(function(filePath) {
        jake.Task['compile'].reenable();
        jake.Task['compile'].invoke(filePath);
    });
    complete();
});

task('push', {async: true}, function(){
    console.log('pushing changes');
    cp.exec('git add . && git commit -m\'deployment\' && git push origin gh-pages', function(error, stderr, stdout) {
        if (error) {
            console.error(error);
            fail(error.message);
            return;
        }
        if (stderr) {
            fail(stderr);
            return;
        }
        console.log('deployment done');
        complete();
    });
});

task('deploy', ['build','push'], function(){
});