var headersObj = new Object();
{
    var headerCells = document.getElementById("triggerTable").rows[0].children;
    for (var i = 0; i < headerCells.length; i++)  {
        var header = headerCells[i].innerHTML;
        headersObj[header] = i;
    }
}
//console.log('headersObj:' + JSON.stringify(headersObj));
var checkCol = headersObj["del"];
var stationCol = headersObj["station"];
var channelCol = headersObj["channel"];
var valCol = headersObj["val"];
var indexCol = headersObj["ind"];
var nameCol = headersObj["name"];
var triggerCol = headersObj["trigger"];
var initCol = headersObj["init_level"];
var stopCol = headersObj["stop_level"];
var sessionId = Math.floor(Math.random() * 1000000) + 1;
var staCol = headersObj["sta"];
var ltaCol = headersObj["lta"];
var filterCol = headersObj["filter"];
var freqminCol = headersObj["freqmin"];
var freqmaxCol = headersObj["freqmax"];

//var needsUpdate = false;

// this will force reload on every visit
window.onbeforeunload = function() {
	console.log('before unload');
	//needsUpdate = true;
};

console.log("init page");
initPage();

var stationsData;

function checkInt(value) {
		return /^\d*$/.test(value) && (value === "" || parseInt(value) < 100);
}

function checkFloat(value) {
	return /^-?\d*[.,]?\d*$/.test(value) && (value === "" || parseFloat(value) < 100);
}

function setInputFilter(textbox, inputFilter) {
	  ["input", "keydown", "keyup", "mousedown", "mouseup", "select", "contextmenu", "drop"]
	  	.forEach(function(event) {
	  				textbox.addEventListener(event, function() {
	  					if (inputFilter(this.value)) {
	  						this.oldValue = this.value;
	  						this.oldSelectionStart = this.selectionStart;
	  						this.oldSelectionEnd = this.selectionEnd;
	  					} else if (this.hasOwnProperty("oldValue") && this.oldValue != "") {
	  						this.value = this.oldValue;
	  						this.setSelectionRange(this.oldSelectionStart, this.oldSelectionEnd);
	  					} else {
	  						this.value = "0";
	  					}
	  				});
	  			});
}

function initPage() {
	var xhr = new XMLHttpRequest();
	var headerRow = document.getElementById("triggerTable").rows[0];
	headerRow.children[staCol].innerHTML += "<br/>(len)";
	headerRow.children[indexCol].style.display = "none";
	xhr.open("POST", "initTrigger", true);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function () {
		if (xhr.readyState === 4 && xhr.status === 200) {
			stationsData = JSON.parse(xhr.responseText);
//		    console.log("respObj:" + respObj + "\nresponseText:" + xhr.responseText +
//		    		"\nkeys:" + Object.keys(respObj) + "\n" + respObj.keys);
		    var stations = Object.keys(stationsData);
		    stations.sort();
			var rows = document.getElementById("triggerTable").rows;
			for (var row of Array.from(rows).slice(1))	{
				row.cells[indexCol].style.display = "none";
				var channelCell = row.cells[channelCol];
				var stationCell = row.cells[stationCol];
				var station = getStation(stationCell);
				setStationsCell(stations, stationCell);
				setUnits(row);
				setFrequencesVisibility(row);
				if (station in stationsData)	{
					var channels = stationsData[station]["channels"];
					setChannelsCell(channels, channelCell);
				}
				var staNode = row.cells[staCol].children[0];
				var ltaNode = row.cells[ltaCol].children[0];
				var initNode = row.cells[initCol].children[0];
				var stopNode = row.cells[stopCol].children[0];
				setInputFilter(staNode, checkInt);
				setInputFilter(ltaNode, checkInt);
				setInputFilter(initNode, checkFloat);
				setInputFilter(stopNode, checkFloat);
				for (var numNode of [staNode, ltaNode, initNode, stopNode])	{
					numNode.addEventListener( "change", function() {if (this.value == "") {this.value = 0;};} );
				};
			}
		}
	};
//	rows.forEach(function (row) {
//	    row.cells[valCol].innerHTML = 0 + "";
//	})
	xhr.send();
}

function apply_save() {
	var headerRow = document.getElementById("triggerTable").rows[0];
	headerRow.children[staCol].innerHTML = "sta";
	genNames();
    apply();
    sendHTML();
    setTimeout(nullifyVals, 3000);
    headerRow.children[staCol].innerHTML += "<br/>(len)";
    //console.log('timer started');
}

function apply() {
    //alert('apply');
	var xhr = new XMLHttpRequest();
	var url = "apply";
	xhr.open("POST", url, true);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function () {
		if (xhr.readyState === 4 && xhr.status === 200) {
			var json = JSON.parse(xhr.responseText);
			//console.log(json);
			//document.getElementById("counter").value = json.counter;
			//alert('Response arrived!');
		}
	};
	var rows = document.getElementById("triggerTable").rows;
	var channels = [];
	for (var j = 1; j < rows.length; j++) {
		var row = rows[j];
		var channelCell = row.cells[channelCol];
		var nameCell = row.cells[nameCol];
		//console.log('nameCell:' + nameCell.innerHTML);
//		console.log('channel cell child:' + channelCell.children[0].innerHTML);
//		console.log('option html:' + channelCell.children[0].options[0].innerHTML);
		var options = channelCell.children[0].options;
		var selectedIndex = options.selectedIndex;
//		console.log('selected index:' + options.selectedIndex);
		var channel = options[selectedIndex].text;
		channels.push(channel);
		var valCell = row.cells[valCol];
		//valCell.innerHTML = 0;
	};
	setSelectedChannels(channels);
	setSelectedTriggers();
	setSelectedStations();
	setLevels();
	setFilters();
	var data = JSON.stringify({"apply": 1, "channels":  channels.join(" ")});
	xhr.send(data);
}

function sendHTML() {
	var xhr = new XMLHttpRequest();
	var url = "save";
	xhr.open("POST", url, true);
	xhr.setRequestHeader("Content-Type", "application/html");
	var pageHTML = "<html>\n" + document.documentElement.innerHTML + "\n</html>";
	//console.log("pageHTML:" + pageHTML);
	var data = JSON.stringify({"html": pageHTML, "sessionId":  sessionId});
	xhr.send(data);
}

function nullifyVals()	{
	var rows = document.getElementById("triggerTable").rows;
	for (var j = 1; j < rows.length; j++) {
		var imgNode = rows[j].cells[valCol].children[0];
	    imgNode.setAttribute("src", "img\\circle-gray.jpg");
	}
}

setTimeout(updateFunc, 1000);

function updateFunc() {
	var xhr = new XMLHttpRequest();
	var url = "trigger";
	xhr.open("POST", url, true);
	//xhr.timeout = 10000;
	xhr.setRequestHeader("Content-Type", "application/json");
	var pageMap = getFromHtml();
	xhr.onreadystatechange = function () {
		if (xhr.readyState === 4) {
		    if (xhr.status === 200)   {
                console.log('response:' + xhr.responseText);
                var json = JSON.parse(xhr.responseText);
                var triggers = json.triggers;
                setTriggerVals(triggers);
            } else  {
                nullifyVals();
                location.reload();
            }
            setTimeout(updateFunc, 1000);
		}
	};
	pageMap["sessionId"] = sessionId;
	var data = JSON.stringify(pageMap);
	console.log('data to send:' + data);
	xhr.send(data);
}

function pauseCounter() {
    clearInterval(myVar);
}

function resumeCounter() {
    myVar = setInterval(myTimer, 1000);
}

function getFromHtml()	{
	var rows = document.getElementById("triggerTable").rows;
	var triggers = {};
	var channels = [];
	var i;
	if (rows.length > 1) {
		for (i = 1; i < rows.length; i++)	{
		    var row = rows[i];
		    var imgNode = row.cells[valCol].children[0];
		    var src = imgNode.getAttribute("src");
		    var triggerVal = 1;
		    if (src == "img\\circle-gray.jpg")	{
		    	triggerVal = 0;
		    }
		    var ind = parseInt(row.cells[indexCol].innerHTML);
			triggers[ind] = triggerVal;
		}
		var options = rows[1].cells[channelCol].children[0].options;
		for (i = 0; i < options.length; i++) {
		    var optionNode = options[i];
		    channels.push(optionNode.text);
		}
		channels = [...(new Set(channels))].sort();
	}
	return {triggers : triggers, channels : channels};
}

function getSelectedChannels () {
	var rows = document.getElementById("triggerTable").rows;
	var selectedChannels = [];
	if (rows.length > 1) {
		for (var i = 1;  i < rows.length; i++) {
			options = rows[i].cells[channelCol].children[0].children;
			var selectedIndex = options.selectedIndex;
			var selectedChannel = options[selectedIndex].text;
			selectedChannels.push(selectedChannel);
		}
	}
	return selectedChannels;
}

function setTriggerVals(triggers) {
	var rows = document.getElementById("triggerTable").rows;
	if (rows.length > 1) {
		for (var i = 1;  i < rows.length; i++) {
		    row = rows[i];
		    ind = row.cells[indexCol].innerHTML;
		    //console.log('ind:' + ind + ' triggers keys:' + Object.keys(triggers));
		    if (ind in triggers) {
		    	var imgNode = row.cells[valCol].children[0];
		    	var src = "img\\circle-gray.jpg";
		    	if (triggers[ind])	{
		    		src = "img\\circle-green.jpg";
		    	}
			    imgNode.setAttribute("src", src);
			}
		}
	}
}

function setChannelsList(channels) {
	var rows = document.getElementById("triggerTable").rows;
	if (rows.length > 1) {
		for (var i = 1;  i < rows.length; i++) {
			var channelCell = rows[i].cells[channelCol];
			var options = channelCell.children[0].options;
			var selectedIndex = options.selectedIndex;
//			console.log("selectedIndex:" + selectedIndex);
			var selectedChannel = options[selectedIndex].text;
			channelCell.children[0].innerHTML = "";
			channels.forEach(function (channel) {
				var optionNode = document.createElement("option");
				optionNode.text = channel;
				if (channel == selectedChannel) {
					optionNode.setAttribute("selected", "selected");
				}
				channelCell.children[0].appendChild(optionNode);
			});
		}
	}
}

function setChannelsCell(channels, channelCell)	{
	var options = channelCell.children[0].options;
	var selectedChannel = options[options.selectedIndex].text;
	var channels_cur = channels.slice();
	if (!channels_cur.includes(selectedChannel))	{
		channels_cur.push(selectedChannel);
	};
	channelCell.children[0].innerHTML = "";
	channels_cur.forEach(function (channel) {
		var optionNode = document.createElement("option");
		optionNode.text = channel;
		if (channel == selectedChannel) {
			optionNode.setAttribute("selected", "selected");
		}
		channelCell.children[0].appendChild(optionNode);
	});
}

function setSelectedChannels(selectedChannels) {
	var rows = document.getElementById("triggerTable").rows;
	if (rows.length > 1) {
		for (var i = 1;  i < rows.length; i++) {
			var options = rows[i].cells[channelCol].children[0].options;
			var selectedChannel = selectedChannels[i-1];
			var present = false;
			for (var j = 0; j < options.length; j++)	{
				if (options[j].text == selectedChannel) {
					options.selectedIndex = j;
					options[j].setAttribute("selected", "selected");
					present = true;
				} else {
					options[j].removeAttribute("selected");
				}
			}
			if (present == false) {
				var optionNode = document.createElement("option");
				optionNode.text = selectedChannel;
				optionNode.setAttribute("selected", "selected");
				document.getElementById("triggerTable").rows[i].cells[channelCol].children[0].appendChild(optionNode);
				selectedIndex = options.length - 1;
				options.selectedIndex = selectedIndex;
			}
		}
	}
}

function setSelectedTriggers() {
	var rows = document.getElementById("triggerTable").rows;
	if (rows.length > 1) {
		for (var i = 1;  i < rows.length; i++) {
			var options = rows[i].cells[triggerCol].children[0].options;
			for (var j = 0; j < options.length; j++)	{
				var option = options[j];
				if (j == options.selectedIndex) {
					option.setAttribute("selected", "selected");
				}
				else {
					option.removeAttribute("selected");
				}
			}
		}
	}
}

function getDefaultChannels() {
	var channels = [];
	var rows = document.getElementById("triggerTable").rows;
	if (rows.length > 1) {
		for (var i = 1;  i < rows.length; i++) {
			var channelCell = rows[i].cells[channelCol];
			var options = channelCell.children[0].options;
			var channel;
			for (var j = 0; j < options.length; j++)	{
				optionNode = options[j];
				if (optionNode.hasAttribute("selected"))	{
					channel = optionNode.text;
				}
			}
			if (channel == undefined)	{
				selectedIndex = options.selectedIndex;
				channel = options[selectedIndex].text;
			}
			channels.push(channel);
		}
	}
	return channels;
}

function addTrigger() {
    var table = document.getElementById("triggerTable");
    var rows = table.rows;
    var len = rows.length
    var row = rows[len - 1].cloneNode(true);
    var ind = parseInt(row.cells[indexCol].innerHTML) + 1;
    row.cells[indexCol].innerHTML = ind;
    row.cells[nameCol].children[0].value = "";
    table.children[0].appendChild(row);
}

function getStation(stationCell)	{
	var options = stationCell.children[0].options;
	return options[options.selectedIndex].text;
}

function setStationsCell(stations, stationCell)	{
	var selectedStation = getStation(stationCell);
	var stations_cur = stations.slice();
	if (!stations_cur.includes(selectedStation))	{
		stations_cur.push(selectedStation);
	};
	stationCell.children[0].innerHTML = "";
	stations_cur.forEach(function (station) {
		var optionNode = document.createElement("option");
		optionNode.text = station;
		if (station == selectedStation) {
			optionNode.setAttribute("selected", "selected");
		}
		stationCell.children[0].appendChild(optionNode);
	});
}

function setSelectedStations(stations, stationCell)	{
	var rows = document.getElementById("triggerTable").rows;
	for (var row of Array.from(rows).slice(1))	{
		var stationCell = row.cells[stationCol];
		var selectedStation = getStation(stationCell);
		var options = stationCell.children[0].options;
		for (var option of Array.from(options))	{
			if (option.text == selectedStation)	{
				option.setAttribute("selected", "selected");
			} else	{
				option.removeAttribute("selected");
			}
		}
	}
}

function stationChange(node)	{
	var station = node.value;
	var row = node.parentNode.parentNode;
	//console.log("row innerHTML:" + row.innerHTML);
	if (!stationsData)	{
		console.log("stations data is unavailable");
	} else	{
		setUnits(row);
		var channelCell = row.cells[channelCol];
		var channels = stationsData[station]["channels"];
		setChannelsCell(channels, channelCell);
	}
}

function setLevels()	{
	var rows = document.getElementById("triggerTable").rows;
	for (var row of Array.from(rows).slice(1))	{
		for (var header of ["init_level", "stop_level", "sta", "lta", "name", "freqmin", "freqmax"])	{
			var inputElement = row.cells[headersObj[header]].children[0];
			inputElement.setAttribute("value", inputElement.value);
		}
	}
}

function setFilters()	{
	var rows = document.getElementById("triggerTable").rows;
	for (var row of Array.from(rows).slice(1))	{
		var checkElement = row.cells[filterCol].children[0];
		setCheckedNode(checkElement);
	}
}

function setUnits(row)	{
	var unitsNode  = row.cells[initCol].children[1];
	var unitsNode2 = row.cells[stopCol].children[1];
	var units = "";
	var trigger_value = row.cells[triggerCol].children[0].value;
	var stalta_trigger = trigger_value == "sta_lta";
	var level_trigger = trigger_value == "level";
	var staNode = row.cells[staCol].children[0];
	var ltaNode = row.cells[ltaCol].children[0];
	if (stalta_trigger)	{
		//console.log("stalta");
		ltaNode.style.display = "inline";
	}	else	{
		//console.log("not stalta");
		ltaNode.style.display = "none";
		units = "V";
		var stationCell = row.cells[stationCol];
		var station = getStation(stationCell);
		if (station in stationsData)	{
			units = stationsData[station]["units"];
		}
	}
	if (level_trigger)	{
		console.log("level trigger");
		staNode.style.display = "none";
	}	else	{
		staNode.style.display = "inline";
	}
	unitsNode.innerHTML  = units;
	unitsNode2.innerHTML = units;
	var filterNode = row.cells[filterCol].children[0];
	if (filterNode.checked)	{

	}
}

function setFrequencesVisibility(row)	{
	var filterNode = row.cells[filterCol].children[0];
	var freqminNode = row.cells[freqminCol].children[0];
	var freqmaxNode = row.cells[freqmaxCol].children[0];
	if (filterNode.checked)	{
		freqmaxNode.style.display = "inline";
		freqminNode.style.display = "inline";
	}	else	{
		freqmaxNode.style.display = "none";
		freqminNode.style.display = "none";
	}
}

function genName(station, channel, trigger, name, names)	{
	//console.log("name:" + name);
	if (!name)	{
		//console.log("name is empty, generate name");
		if (trigger == "RMS")	{
			name = "rms";
		}	else if (trigger == "level")	{
			name = "levl";
		}	else {
			name = "slta";
		}
		name += station.substring(station.length - 1, station.length).toUpperCase();
		name += channel.substring(channel.length - 1, channel.length).toUpperCase();
		//console.log("generated candidate name:" + name);
	}
	if (names.has(name))	{
		//console.log("names has name " + name);
		var newName;
		for (var i = 2; i < 20; i++) {
			  newName = name + i;
			  //console.log("candidate name:" + newName);
			  if (names.has(newName) == false)	{
				  //console.log("candidate name is OK");
				  name = newName;
				  break;
			  }
		}
	}
	//console.log("generated name:" + name);
	return name;
}

function genNames()	{
	var names = new Set();
	var rows = document.getElementById("triggerTable").rows;
	for (var row of Array.from(rows).slice(1))	{
		var cells = row.cells;
	    var name = cells[nameCol].children[0].value;
	    //console.log("name:" + name);
//	    if (!name) {
//	    	console.log("name is false");
//	    }
//	    console.log("name value:" + name);
	    var station = cells[stationCol].children[0].value;
	    var channel = cells[channelCol].children[0].value;
	    var trigger = cells[triggerCol].children[0].value;
	    name = genName(station, channel, trigger, name, names);
	    //console.log("set attribute:" + name);
	    cells[nameCol].children[0].value = name;
	    //document.getElementById("triggerTable").rows[i].cells[nameCol].children[0].setAttribute("value", name);
	    //console.log("after setting attribute:" + cells[nameCol].innerHTML);
	    names.add(name);
    }
}

function setCheckedNode(node)	{
	if (node.checked)	{
		node.setAttribute("checked", "checked");
	}	else	{
		node.removeAttribute("checked");
	}
}

function removeTrigger(row)	{
	var table = document.getElementById("triggerTable");
	var rows = Array.from(table.rows).slice(1);
	if (rows.length > 1)	{
		table.children[0].removeChild(row);
	}
}

