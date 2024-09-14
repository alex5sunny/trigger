const DATA_LEN = 20000

var headersObj = new Object();
{
	var row = document.getElementById("rulesTable").rows[0];
    var headerCells = row.children;
    for (var i = 0; i < headerCells.length; i++)  {
        var header = headerCells[i].innerHTML;
        headersObj[header] = i;
    }
}

var triggersDic;

var actionsDic;

var checkCol = headersObj["del"];
var ruleIdCol = headersObj["rule_id"];
var formulaCol = headersObj["formula"];
var ruleValCol = headersObj["val"];
var actionCol = headersObj["actions"];

var triggersObj = {};

var rulesObj = getRulesObj();

var ruleTimes = {};

var sessionId = Math.floor(Math.random() * 1000000) + 1;

initFunc();

function updateTriggers (triggersObj, ruleCell) {
	var children = ruleCell.children;
	for (var i = 0; i < children.length; i++)	{
		var node = children[i];
		//console.log('nodeName:' + node.nodeName);
		if (node.nodeName == "IMG") 	{
			var triggerNode = children[i - 1];
			var options = triggerNode.options;
			var selectedIndex = triggerNode.selectedIndex;
			var triggerName = options[selectedIndex].text;
			//console.log('triggerIdStr:' + triggerIdStr);
			var triggerIdStr;
			for (triggerIdStr in triggersDic)	{
				if (triggerName == triggersDic[triggerIdStr])	{
					break;
				}
			}
			var triggerVal = triggersObj[triggerIdStr];
			//console.log('triggerVal:' + triggerVal);
			var src;
			if (triggerVal)	{
				src = "img\\green16.jpg";
			}	else	{
				src = "img\\gray16.jpg";
			}
			node.setAttribute("src", src);
		}
	}
}

function updateRules(rulesObj)	{
    var table = document.getElementById("rulesTable");
    var rows = table.rows;
    for (var i = 1; i < rows.length; i++)	{
    	var row = rows[i];
    	var imgNode = row.cells[ruleValCol].children[0];
      	var ruleId = row.cells[ruleIdCol].innerHTML;
		var src;
       	//console.log('ruleId:' + ruleId + ' ruleVal:' + rulesObj[ruleId]);
      	if (ruleId in rulesObj)	{
      		if (rulesObj[ruleId])	{
      			src = "img\\circle-red.jpg";
      		}	else	{
      			src = "img\\circle-gray.jpg";
      		}
      		imgNode.setAttribute("src", src);
      	}
    }
}


var GRAPH_DATA = {ch1: [], ch2: [], ch3: []}

var MARKERS_DATA = new Map()

function updateFunc () {
	var xhr = new XMLHttpRequest();
	xhr.open("POST", "rule", true);
	//xhr.timeout = 10000;
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function () {
		if (xhr.readyState === 4) {
		    if (xhr.status === 200)    {
                var respObj = JSON.parse(xhr.responseText);
				if ('endtime' in respObj)	{
					// console.log('npts:' + respObj['ch1'].length);
					GRAPH_DATA['endtime'] = new Date(respObj['endtime'])
					for (var chan of ['ch1', 'ch2', 'ch3']) {
						GRAPH_DATA[chan].push(...respObj[chan])
						if (GRAPH_DATA[chan].length > DATA_LEN)	{
							GRAPH_DATA[chan].splice(0, GRAPH_DATA[chan].length - DATA_LEN)
						}
						// var av = GRAPH_DATA[chan].reduce((su, a) => su + a, 0) / GRAPH_DATA[chan].length;
						// GRAPH_DATA[chan] = GRAPH_DATA[chan].map(a=>a - av + 0.005*(1-i));
					}
				} else	{
					console.log('response:' + xhr.responseText);
				}
				if ('events' in respObj)	{
				    document.getElementById('ruleTimes').innerHTML = ''
					respObj.events = JSON.parse(respObj.events);
					console.log('events:' + JSON.stringify(respObj.events))
					for (var ev of respObj.events)	{
						var evStr = ''
						for (var ke of ['t1', 't2', 't3'])	{
							evStr += ke + ':' + ev[ke].split(' ').at(-1) + '\xa0\xa0\xa0'
						}
						for (var ke of ['azimuth1', 'azimuth2'])	{
							evStr += ke + ':' + ev[ke] + '\xa0\xa0\xa0'
						}
						document.getElementById('ruleTimes').innerHTML = evStr + '<br>'
							+ document.getElementById('ruleTimes').innerHTML
						// var d = new Date(ev.t3)
						// console.log('ev:' + ev + ' t3:' + ev.t3 + ' d:' + d)
						MARKERS_DATA.set((new Date(ev.t3)).getTime(), {azimuth1: ev.azimuth1, azimuth2: ev.azimuth2});
						// console.log('keys:' + Array.from( MARKERS_DATA.keys() ));
					}
				}
                triggersObj = respObj['triggers'];
                rulesObj = respObj['rules'];
                //console.log('rulesObj from server:' + JSON.stringify(rulesObj));
                updateRules(rulesObj);
                var rows = document.getElementById("rulesTable").rows;
                for (var i = 1; i < rows.length; i = i + 1)	{
                    var row = rows[i];
                    var ruleCell = row.cells[formulaCol];
                    updateTriggers(triggersObj, ruleCell);
                }
            }   else    {
                nullifyVals();
                location.reload();
            }
            setTimeout(updateFunc, 1000);
		}
	};
	var rulesObj = getRulesObj();
	//console.log('rulesObj:' + JSON.stringify(rulesObj));
	var data = {triggers: triggersObj, sessionId: sessionId, rules: rulesObj};
	//console.log('data to send:' + JSON.stringify(data));
	xhr.send(JSON.stringify(data));
}

function initFunc () {
	var xhr = new XMLHttpRequest();
	xhr.open("POST", "initRule", true);
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function () {
		if (xhr.readyState === 4 && xhr.status === 200) {
		    //console.log('response:' + xhr.responseText);
			var responseObj = JSON.parse(xhr.responseText);
			triggersDic = responseObj['triggers'];
			actionsDic = responseObj['actions'];
			console.log("actions dic:" + JSON.stringify(actionsDic));
			var triggersIds = [];
			for (triggerId in triggersDic)	{
				triggersIds.push(triggerId);
			}
			triggersIds.sort();
			var triggerNames = [];
			for (var triggerId of triggersIds)	{
				triggersObj[triggerId] = 0;
				triggerNames.push(triggersDic[triggerId]);
			}

			var actionIds = [];
			for (actionId in actionsDic)	{
				actionIds.push(actionId);
			}
			actionIds.sort();

			var rows = document.getElementById("rulesTable").rows;
			var triggerNode = rows[1].cells[formulaCol].children[0];
			var triggerOptions = triggerNode.children;
			var actionOptions = rows[1].cells[actionCol].children[0].options;
			var prevTriggerIds = [];
			var prevActionIds = [];
			for (var option of triggerOptions)	{
				prevTriggerIds.push(option.getAttribute("trigger_id"));
			}
			for (var option of actionOptions)	{
				prevActionIds.push(option.getAttribute("action_id"));
			}
			rows[0].cells[ruleIdCol].style.display = "none";
			for (var i = 1; i < rows.length; i = i + 1)	{
				var row = rows[i];
				row.cells[ruleIdCol].style.display = "none";
				var ruleCell = row.cells[formulaCol];
				fillTriggers(ruleCell);
				var actionCell = row.cells[actionCol];
				fillActions(actionCell, prevActionIds);
			}
			setTimeout(updateFunc, 1000);
		}
	}
	console.log('triggers obj:' + triggersObj);
	xhr.send();
}

function fillTriggers (ruleCell)	{
	for (var triggerNode of ruleCell.children)	{
		if (triggerNode.nodeName != "SELECT" ||
				!triggerNode.children[0].hasAttribute("trigger_id"))	{
			continue;
		}
		var selectedOption = triggerNode.options[triggerNode.selectedIndex];
		//console.log('selected option:' + selectedOption.outerHTML);
		selectedOption = selectedOption.cloneNode(true);
		//console.log('cloned option:' + selectedOption.outerHTML);
		var selectedId = selectedOption.getAttribute("trigger_id");
		//console.log('selected id:' + selectedId);
		triggerNode.innerHTML = '';
		var idPresent = false;
		for (var triggerId in triggersDic)	{
			var optionNode = document.createElement("option");
			optionNode.text = triggersDic[triggerId];
			optionNode.setAttribute("trigger_id", triggerId);
			if (triggerId == selectedId || selectedOption.text == triggersDic[triggerId]) {
				optionNode.setAttribute("selected", "selected");
				idPresent = true;
			}
			triggerNode.appendChild(optionNode);
		}
		//console.log('triggerNode before append:' + triggerNode.innerHTML);
		if (!idPresent)	{
			triggerNode.appendChild(selectedOption);
		}
		//console.log('triggerNode after append:' + triggerNode.innerHTML);
	}
}

function fillActions (actionCell, prevIds)	{
	for (var actionNode of actionCell.children)	{
		if (actionNode.nodeName != "SELECT")	{
			continue;
		}
		var selectedOption = actionNode.options[actionNode.selectedIndex];
		//console.log('selected option:' + selectedOption.outerHTML);
		selectedOption = selectedOption.cloneNode(true);
		//console.log('cloned option:' + selectedOption.outerHTML);
		var selectedId = selectedOption.getAttribute("action_id");
		//console.log('selected id:' + selectedId);
		actionNode.innerHTML = '';
		var idPresent = false;
		for (var actionId in actionsDic)	{
			console.log('actionId:' + actionId + ' action name:' + actionsDic[actionId])
			var optionNode = document.createElement("option");
			optionNode.text = actionsDic[actionId];
			optionNode.setAttribute("action_id", actionId);
			if (actionId == selectedId || selectedOption.text == actionsDic[actionId]) {
				optionNode.setAttribute("selected", "selected");
				idPresent = true;
			}
			actionNode.appendChild(optionNode);
		}
		if (!idPresent)	{
			actionNode.appendChild(selectedOption);
		}
	}
}

function addRule() {
    var table = document.getElementById("rulesTable");
    var rows = table.rows;
    var len = rows.length
    var row = rows[len - 1].cloneNode(true);
    var ind = parseInt(row.cells[ruleIdCol].innerHTML) + 1;
    row.cells[ruleIdCol].innerHTML = ind;
    table.children[0].appendChild(row);
}

function setSelected(node) 	{
	if (node.nodeName == "SELECT")	{
		var html1 = node.innerHTML;
		var options = node.children;
		var len = options.length;
		var selectedIndex = node.selectedIndex;
		console.log('selected index:' + selectedIndex);
		for (var i = 0; i < options.length; i++)	{
			var option = options[i];
			if (i == selectedIndex)	{
				option.setAttribute("selected", "selected");
			} else	{
				option.removeAttribute("selected");
			}
		}
	}
}

function setValue(elementId)	{
	var node = document.getElementById(elementId);
	var value = node.value;
	node.setAttribute("value", value);
}

function apply()	{
    var table = document.getElementById("rulesTable");
    var rows = table.rows;
    for (var i = 1; i < rows.length; i++)	{
    	var row = rows[i];
    	var ruleCell = row.cells[formulaCol];
    	var children = ruleCell.children;
    	for (var j = 0; j < children.length; j++)	{
    		var node = children[j];
       		setSelected(node);
    	}
    	var actionCell = row.cells[actionCol];
    	children = actionCell.children;
    	for (var actionNode of children)	{
    		setSelected(actionNode);
    	}
    }
	var objToSend = {}
	for (var elementId of ['lat1', 'lon1', 'lat2', 'lon2', 'lat3', 'lon3', 'ch1', 'ch2', 'ch3'])	{
		objToSend[elementId] = document.getElementById(elementId).value
	}

	var xhr = new XMLHttpRequest();
	var url = "applyRules";
	xhr.open("POST", url, true);
	xhr.setRequestHeader("Content-Type", "application/html");

	var data = JSON.stringify(objToSend);
	xhr.send(data);
	setTimeout(nullifyVals, 3000);
}

function nullifyVals()	{
	//console.log('time out');
	var rows = document.getElementById("rulesTable").rows;
	for (var i = 1; i < rows.length; i++) {
		var imgNode = rows[i].cells[ruleValCol].children[0];
		imgNode.setAttribute("src", "img\\circle-gray.jpg");
		ruleCell = rows[i].cells[formulaCol];
		for (var triggerImgNode of ruleCell.children)	{
		    if (triggerImgNode.nodeName == "IMG" && triggerImgNode.hasAttribute("src"))  {
		        triggerImgNode.setAttribute("src", "img\\gray16.jpg");
		    }
		}
	}
}

function getRulesObj()	{
	var rulesObj = {};
    var table = document.getElementById("rulesTable");
    var rows = table.rows;
    for (var i = 1; i < rows.length; i++)	{
    	var row = rows[i];
    	var ruleId = parseInt(row.cells[ruleIdCol].innerHTML);
	    var src = row.cells[ruleValCol].children[0].getAttribute("src");
	    var ruleVal;
	    if (src == "img\\circle-red.jpg")	{
	    	ruleVal = 1;
	    }	else	{
	    	ruleVal = 0;
	    }
    	rulesObj[ruleId] = ruleVal;
    }
    return rulesObj;
}

function removeRule(row)	{
	var table = document.getElementById("rulesTable");
	var rows = Array.from(table.rows).slice(1);
	if (rows.length > 1)	{
		table.children[0].removeChild(row);
	}
}

function addTrigger(refNode)	{
	var imgNode = refNode.previousElementSibling;
	var triggerNode = imgNode.previousElementSibling;
	var imgNode = imgNode.cloneNode(true);
	var triggerNode = triggerNode.cloneNode(true);

	var triggersCell = refNode.parentNode;
	var nodes = triggersCell.children;
	var node;
	var curNames = [];
	var curTriggerNode;
	for (node of nodes)	{
		if (node.nodeName == "IMG")	{
			curTriggerNode = node.previousElementSibling;
			curNames.push(curTriggerNode.value);
		}
	}
	var nOfTriggers = curNames.length;
	if (nOfTriggers > 7)	{
		return;
	}
	if (nOfTriggers == 4)	{
		node = document.createElement("small");
		node.innerHTML = ">>";
		triggersCell.insertBefore(node, refNode);
		node = node.cloneNode(true);
		triggersCell.insertBefore(node, refNode);
		var brNode = document.createElement("br");
		triggersCell.insertBefore(brNode, node);
	}

	var selected = false;
	for (var option of triggerNode.options)	{
		if (curNames.includes(option.innerHTML) || selected)	{
			option.removeAttribute("selected");
		}	else	{
			option.setAttribute("selected", "selected");
			selected = true;
		}
	}
	var opNode = document.createElement('select');
	opNode.setAttribute("class", "operation");
	for (var op of ["and", "and not", "or", "or not"])	{
		var subNode = document.createElement("option");
		subNode.innerHTML = op;
		opNode.appendChild(subNode);
	}
	opNode.children[0].setAttribute("selected", "selected");
	triggersCell.insertBefore(opNode, refNode);
	triggersCell.insertBefore(triggerNode, refNode);
	triggersCell.insertBefore(imgNode, refNode);
}

function removeTrigger(triggersCell)	{
	var nodes = triggersCell.children;
	var len = nodes.length;
	var i = len - 1;
	//console.log("nodes[i].name:" + nodes[i].name);
	while (nodes[i].nodeName != "IMG")	{
		i = i - 1;
	}
	if (i < 3)	{
		return;
	}
	while (true)	{
		triggersCell.removeChild(nodes[i]);
		i = i - 1;
		if (nodes[i].nodeName == "IMG")	{
			break;
		}
	}
}

function addAction(refNode)	{
	var actionCell = refNode.parentNode;
	var nodes = actionCell.children;
	var len = nodes.length;
	var i = len - 1;
	//console.log("nodes[i].name:" + nodes[i].name);
	while (nodes[i].nodeName != "SELECT")	{
		i = i - 1;
	}
	if (i > 2)	{
		return;
	}
	var actionNode = nodes[i].cloneNode(true);
	var curActions = [];
	for (var j = 0; j <= i; j++)	{
		curActions.push(nodes[j].value);
	}
	var selected = false;
	for (var option of actionNode.options)	{
		if (curActions.includes(option.innerHTML) || selected)	{
			option.removeAttribute("selected");
		}	else	{
			option.setAttribute("selected", "selected");
			selected = true;
		}
	}
	actionCell.insertBefore(actionNode, refNode);
}

function removeAction(actionCell)	{
	var nodes = actionCell.children;
	var len = nodes.length;
	var i = len - 1;
	//console.log("nodes[i].name:" + nodes[i].name);
	while (nodes[i].nodeName != "SELECT")	{
		i = i - 1;
	}
	if (i < 1)	{
		return;
	}
	actionCell.removeChild(nodes[i]);
}

function genArray(ar_len) {
    var ar = []
    for (var i = 0; i < ar_len; i++)  {
        ar[i] = Math.round(Math.random()*10) + 1
    }
    return ar
}

function genTimes(date_time, n)  {
    var times = [date_time]
    var t = date_time
    for (var i = 0; i < n - 1; i++) {
        var t = new Date(t)
        t.setMilliseconds(t.getMilliseconds() - 1)
        times.unshift(t)
    }
    return times
}

function actualizeMarkers()	{
	let keys = Array.from( MARKERS_DATA.keys() );
	// console.log('keys:' + keys)
	for (let ke of keys)	{
		const endtime = GRAPH_DATA['endtime']
		var back_time = new Date(endtime)
		back_time.setSeconds(back_time.getSeconds() - DATA_LEN / 1000)
		// console.log('ke:' + ke + ' back_time:' + back_time)
		if (MARKERS_DATA.has(ke) && (new Date(ke)) < back_time)	{
			MARKERS_DATA.delete(ke);
		}
	}
}

function markY()	{
	var ys = []
	var n = GRAPH_DATA.ch3.length
	var delta = 0.001
	for (const t of MARKERS_DATA.keys()) {
		var ind = Math.round(((new Date(t)) - GRAPH_DATA.endtime + n * delta) / delta);
		ys[ys.length] = GRAPH_DATA.ch3[ind]
	}
	return ys
}

function markTexts()	{
	var texts = []
	var delta = 0.001
	for (const t of MARKERS_DATA.keys()) {
		texts[texts.length] = '<b><i>' + MARKERS_DATA.get(t)['azimuth1'] + '<br>' +
			MARKERS_DATA.get(t)['azimuth2'] + '</i></b>'
	}
	return texts
}

var layout = {
  yaxis: {
    range: [-0.010, 0.010],
  }
};

Plotly.newPlot('graph',
    [
        {
            y: [],
            x: [],
            mode: 'lines',
            line: {color: 'orange'}
        },
        {
            y: [],
            x: [],
            mode: 'lines',
            line: {color: 'green'}
        },
        {
            y: [],
            x: [],
            mode: 'lines',
            line: {color: 'blue'}
        },
        {
            mode: 'markers+text',
            textposition: 'left',
			textfont: {
                size: 15
            },
            line: {color: 'red'},
			marker: {
                size: 20,
                symbol: ['6']
            }
        }
    ]
);


setInterval(function() {
    var times = genTimes(GRAPH_DATA.endtime, GRAPH_DATA.ch1.length)
    actualizeMarkers()
	var markersArray = []
	for (var t of Array.from(MARKERS_DATA.keys()))    {
		markersArray[markersArray.length] = new Date(t)
	}
	var max_val = Math.max(
		Math.max(...GRAPH_DATA.ch1), Math.max(...GRAPH_DATA.ch2), Math.max(...GRAPH_DATA.ch3)
	)
	var data_show = structuredClone(GRAPH_DATA)
	for (var [i, chan] of ['ch1', 'ch2', 'ch3'].entries()) {
		var av = data_show[chan].reduce((su, a) => su + a, 0) / data_show[chan].length;
		data_show[chan] = data_show[chan].map(a=>a - av + 0.5*max_val*(1-i));
	}

    Plotly.update(
        'graph',
        {
            y: [data_show.ch1, data_show.ch2, data_show.ch3, Array(markersArray.length).fill(0.008)],
            x: [times, times, times, markersArray],
            text: [[], [], [], markTexts()]
        }
    )
}, 1000)

