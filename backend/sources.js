var headersObj = new Object();
{
    var headerCells = document.getElementById("sourcesTable").rows[0].children;
    for (var i = 0; i < headerCells.length; i++)  {
        var header = headerCells[i].innerHTML;
        headersObj[header] = i;
    }
}

var checkCol = headersObj["del"];
var stationCol = headersObj["station"];
var hostCol = headersObj["host"];
var portCol = headersObj["port"];
var streamCol = headersObj["stream"];
var outPortCol = headersObj["out port"];

function apply_save() {
	var rows = document.getElementById("sourcesTable").rows;
	for (var row of Array.from(rows).slice(1))	{
		for (var col of [stationCol, hostCol, portCol, outPortCol])	{
			var valNode = row.cells[col].children[0];
			valNode.setAttribute("value", valNode.value);
		}
	}
    sendHTML();
}

function sendHTML() {
	var xhr = new XMLHttpRequest();
	var url = "saveSources";
	xhr.open("POST", url, true);
	xhr.setRequestHeader("Content-Type", "application/html");
	var pageHTML = "<html>\n" + document.documentElement.innerHTML + "\n</html>";
	console.log(pageHTML);
	xhr.send(pageHTML);
}

function genPort(colNum)	{
	var table = document.getElementById("sourcesTable");
	var rows = Array.from(table.rows).slice(1);
	var ports = rows.map(row => {return parseInt(row.cells[colNum].children[0].value)})
	return 1 + Math.max(...ports)
}

function addSource() {
    var table = document.getElementById("sourcesTable");
    var rows = table.rows;
    var len = rows.length
    var row = rows[len - 1].cloneNode(true);
    row.cells[stationCol].children[0].setAttribute("value", "");
	row.cells[portCol].children[0].setAttribute("value", genPort(portCol));
	row.cells[outPortCol].children[0].setAttribute("value", genPort(outPortCol));
    table.children[0].appendChild(row);
}

function removeSource(row)	{
	var table = document.getElementById("sourcesTable");
	var rows = Array.from(table.rows).slice(1);
	if (rows.length > 1)	{
		table.children[0].removeChild(row);
	}
}