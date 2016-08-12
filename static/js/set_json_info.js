var jsonTree = null;

function set_jsonTree(jsonInfo) {
    jsonInfo = jsonInfo.replace(/&quot;/g,'"');
    jsonTree = JSON.parse(jsonInfo);
}
