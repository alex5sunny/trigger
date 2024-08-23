function reverseMap(aMap)	{
	let res = new Map()
	aMap.forEach (function(value, key) {
  		res.set(value, key);
	})
	return res
}

function setOptionsNames(namesMap, table) {
	var rows = table.rows // document.getElementById("triggerTable").rows;
	if (rows.length > 1) {
		for (var i = 1;  i < rows.length; i++) {
			var options = rows[i].cells[triggerCol].children[0].options;
			for (var j = 0; j < options.length; j++)	{
				var option = options[j];
				if (namesMap.has(option.textContent))	{
					option.textContent = namesMap.get(option.textContent)
				}
			}
		}
	}
}
