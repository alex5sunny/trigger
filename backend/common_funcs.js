const RAW_MAP = new Map([
	['outdata', 'выхДанные'],
	['relayA', 'релеА'],
	['relayB', 'релеБ']
])

const COL_NAMES_MAP = new Map([
	['del', 'удал'],
	['station', 'источник'],
	['host', 'ip адрес'],
	['port', 'порт'],
	['stream', 'поток'],
	['out port', 'вых.порт'],
	['channels', 'каналы'],
	['units', 'ед.изм'],
	['formula', 'формула'],
	['actions', 'действия'],
	['check', 'выбор'],
	['name', 'имя'],
	['type', 'тип'],
	['address', 'адрес'],
	['message', 'сообщение'],
	['additional', 'дополнительно'],
	['val', 'индик']
])

const OPTIONS_MAP = new Map([
	['level', 'уровень'],
	['RMS', 'среднекв'],
	['and', 'и'],
	['and not', 'и не'],
	['or', 'или'],
	['or not', 'или не']
])

function reverseMap(aMap)	{
	let res = new Map()
	aMap.forEach (function(value, key) {
  		res.set(value, key);
	})
	return res
}

function setOptionsNames(namesMap, table, colNum) {
	var rows = table.rows // document.getElementById("triggerTable").rows;
	if (rows.length > 1) {
		for (var i = 1;  i < rows.length; i++) {
			var options = rows[i].cells[colNum].children[0].options;
			for (var j = 0; j < options.length; j++)	{
				var option = options[j];
				if (namesMap.has(option.textContent))	{
					option.textContent = namesMap.get(option.textContent)
				}
			}
		}
	}
}

function setHeaders(namesMap, table)	{
	var headerCells = table.rows[0].children;
	for (var i = 0; i < headerCells.length; i++)  {
    	if (namesMap.has(headerCells[i].textContent))	{
			headerCells[i].textContent = namesMap.get(headerCells[i].textContent);
		}
	}
}

function rawReplace(namesMap, table)	{
	var inner_html = table.innerHTML
	namesMap.forEach (function(value, key) {
  		inner_html = inner_html.replaceAll(key, value)
	})
	table.innerHTML = inner_html
}