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

function updateFunc () {
	var xhr = new XMLHttpRequest();
	xhr.open("POST", "rule", true);
	//xhr.timeout = 10000;
	xhr.setRequestHeader("Content-Type", "application/json");
	xhr.onreadystatechange = function () {
		if (xhr.readyState === 4) {
		    if (xhr.status === 200)    {
                console.log('response:' + xhr.responseText);
                respObj = JSON.parse(xhr.responseText);
				if (JSON.stringify(ruleTimes) != JSON.stringify(respObj['rule_times']))	{
					ruleTimes = respObj['rule_times'];
					for (triggerId in ruleTimes) {
						var d = new Date();
						d.setTime(ruleTimes[triggerId] * 1000);
						// * add 'events' label
						// * every trigger on a new line, between triggers two new lines
						// * shorten data format short data, short time, no GMT
						// * output millisecons
						var date_str = d.toLocaleString('sv', {year:'numeric', month:'numeric', day:'numeric', hour:'numeric', minute:'numeric', second:'numeric', fractionalSecondDigits: 3}).replace(',', '.').replace(' ', 'T');
						document.getElementById("ruleTimes").innerHTML += 
							triggersDic[triggerId] + ':' + date_str + '<br>';
					}
					document.getElementById('ruleTimes').innerHTML += '<br>';
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
	console.log('data to send:' + JSON.stringify(data));
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
	for (var elementId of ['lat1', 'lon1', 'lat2', 'lon2', 'lat3', 'lon3'])	{
		setValue(elementId);
	}

	var xhr = new XMLHttpRequest();
	var url = "applyRules";
	xhr.open("POST", url, true);
	xhr.setRequestHeader("Content-Type", "application/html");

	var pageHTML = "<html>\n" + document.documentElement.innerHTML + "\n</html>";
	var data = JSON.stringify({"html": pageHTML, "sessionId":  sessionId});
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

/* function setInputFilter(textbox, inputFilter) {
  ["input", "keydown", "keyup", "mousedown", "mouseup", "select", "contextmenu", "drop"].forEach(function(event) {
    textbox.addEventListener(event, function() {
      if (inputFilter(this.value)) {
        this.oldValue = this.value;
        this.oldSelectionStart = this.selectionStart;
        this.oldSelectionEnd = this.selectionEnd;
      } else if (this.hasOwnProperty("oldValue")) {
        this.value = this.oldValue;
        this.setSelectionRange(this.oldSelectionStart, this.oldSelectionEnd);
      } else {
        this.value = "";
      }
    });
  });
}

for (var id of ['lat1', 'lon1', 'lat2', 'lon2', 'lat3', 'lon3'])	{
	var element = document.getElementById(id);
	setInputFilter(element, 
				   function(value) { 
				   		return /^\d{2}[.,]?\d{6}$/.test(value);
				   });
	element.addEventListener("change", function() {
											if (this.value == "")	{
												this.value = 0;
											};
									   });
}
 */