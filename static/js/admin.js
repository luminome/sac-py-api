import {eztext} from "./eztext.js";

function do_callback(callback, value, args=null){
	if (callback && typeof(callback) === "function") callback(value, args);
}

const Base64 = {

    // private property
    _keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",

    // public method for encoding
    encode : function (input) {
        let output = "";
        let chr1, chr2, chr3, enc1, enc2, enc3, enc4;
        let i = 0;

        input = Base64._utf8_encode(input);

        while (i < input.length) {

            chr1 = input.charCodeAt(i++);
            chr2 = input.charCodeAt(i++);
            chr3 = input.charCodeAt(i++);

            enc1 = chr1 >> 2;
            enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
            enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
            enc4 = chr3 & 63;

            if (isNaN(chr2)) {
                enc3 = enc4 = 64;
            } else if (isNaN(chr3)) {
                enc4 = 64;
            }

            output = output +
            this._keyStr.charAt(enc1) + this._keyStr.charAt(enc2) +
            this._keyStr.charAt(enc3) + this._keyStr.charAt(enc4);
        }
        return output;
    },

    // public method for decoding
    decode : function (input) {
        var output = "";
        var chr1, chr2, chr3;
        var enc1, enc2, enc3, enc4;
        var i = 0;

        input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

        while (i < input.length) {

            enc1 = this._keyStr.indexOf(input.charAt(i++));
            enc2 = this._keyStr.indexOf(input.charAt(i++));
            enc3 = this._keyStr.indexOf(input.charAt(i++));
            enc4 = this._keyStr.indexOf(input.charAt(i++));

            chr1 = (enc1 << 2) | (enc2 >> 4);
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            chr3 = ((enc3 & 3) << 6) | enc4;

            output = output + String.fromCharCode(chr1);

            if (enc3 != 64) {
                output = output + String.fromCharCode(chr2);
            }
            if (enc4 != 64) {
                output = output + String.fromCharCode(chr3);
            }
        }

        output = Base64._utf8_decode(output);

        return output;
    },

    // private method for UTF-8 encoding
    _utf8_encode : function (string) {
        string = string.replace(/\r\n/g,"\n");
        let utftext = "";

        for (let n = 0; n < string.length; n++) {

            let c = string.charCodeAt(n);

            if (c < 128) {
                utftext += String.fromCharCode(c);
            }
            else if((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);
            }
            else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);
            }
        }
        return utftext;
    },

    // private method for UTF-8 decoding
    _utf8_decode : function (utftext) {
        var string = "";
        var i = 0;
        var c = c1 = c2 = 0;

        while ( i < utftext.length ) {

            c = utftext.charCodeAt(i);

            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            }
            else if((c > 191) && (c < 224)) {
                c2 = utftext.charCodeAt(i+1);
                string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            }
            else {
                c2 = utftext.charCodeAt(i+1);
                c3 = utftext.charCodeAt(i+2);
                string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }
        }
        return string;
    }
}


async function uiBasicLoader(resource_obj_list, prog_callback=null) {
	let container = [];

	const get_opts = (obj) => {
		if(obj.register){
			const cred = {'username':'admin','password':obj.v.pw};
			return {
				method: 'POST',
				headers: {
					'mode':'cors',
					'Accept': 'application/json, text/plain, */*',
					'Content-Type': 'application/json',
					'x-api-key': obj.v.kw
				},
				body: JSON.stringify(cred)
			}
		}else if(obj.login) {
			return {
				method: 'POST',
				headers: {
					'Authorization': obj.v.token ? 'Basic ' + Base64.encode(obj.v.token+':unused') : 'Basic ' + Base64.encode('admin:' + obj.v.pw),
					'mode': 'cors',
					'Accept': 'application/json, text/plain, */*',
					'Content-Type': 'application/json',
					'x-api-key': obj.v.kw
				},
				body: JSON.stringify(obj)
			}
		}else if(obj.modify) {
			return {
				method: 'POST',
				headers: {
					'Authorization': 'Bearer '+obj.tx_token,
					'mode': 'cors',
					'Accept': 'application/json, text/plain, */*',
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(obj)
			}
		}else if(obj.acquire) {
			return {
				method: 'POST',
				headers: {
					'mode': 'cors',
					'Accept': 'application/json, text/plain, */*',
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(obj)
			}
		}else{
			return {
			  headers: {
				'mode':'cors'
			  }
			}
		}
	}

	resource_obj_list.forEach(obj => {
		if (prog_callback) do_callback(prog_callback, 1, obj);
		let ref = fetch(obj.url, get_opts(obj))
		.then(response => {
			obj.size = Number(response.headers.get("content-length"));
			return response.text();
		})
		.then(function (text) {
			if(prog_callback) do_callback(prog_callback, -1, obj);
			try {
				return obj.type === 'json' ? JSON.parse(text) : text;
			}catch(error) {
				return [text, error];
			}


		})
		.catch((error) => {
            if(prog_callback) do_callback(prog_callback, -1, obj);
			console.log(error.status, error);
			return error;
		})
		container.push(ref);
	});

	const done = await Promise.all(container);
	resource_obj_list.forEach((obj,i) => obj.raw = done[i]);
	return resource_obj_list;
}

console.log('running locally');
const utf8Encode = new TextEncoder();

const resources = {}

function responder(dom_tgt, trace_tgt){

	const field_struct = [
		{n:'div', id: 'message', label:'MSG'},
		{n:'input', id: 'path', label:'PATH'},
		{n:'div', id: 'status', label:'RS'},
		{n:'div', id: 'time', label:'TD'},
		{n:'div', id: 'command', label:'CMD'}
	]

	function set_field(field, value){
		if(field.tagName === 'INPUT') return field.value = value;
		if(field.tagName === 'DIV') return field.innerHTML = value;
	}


	function update(obj){
		console.log(obj);
		let path = null;
		let file = null;
		let link = null;
		let file_type = null;
		//let message = obj.message ?? null;

		if(obj.data){
			link = obj.data.link ?? false;
			path = obj.data.path ?? false;
			file = obj.data['file-body'] ?? false;

			if(link){
				re.link_node.style.display = ['none','block'][+(link !== false)];
				re.link_node.innerHTML = link;
			}

			if(path){
				if(path.indexOf('.') !== -1){
					file_type = path.split('.').pop();
				}
			}

			if(file){
				if(file_type === 'json' || file_type === null){
					JAM.set_text(JSON.stringify(file, re.json_cleaner, '\t'));
				}else{
					JAM.set_text(`${file.toString()}`);
				}
			}
		}

		field_struct.map((f,i) => {
			if(obj.hasOwnProperty(f.id)) set_field(re.fields[i], obj[f.id]);
			if(f.id === 'path') set_field(re.fields[i], `${path}`);
		})
		//
		//
		//
		//
		// if(obj_format === 'json' || obj_format === null){
		// 	JAM.set_text(JSON.stringify(output_obj, re.json_cleaner, '\t'));
		// }else{
		// 	JAM.set_text(`${output_obj.toString()}`);
		// }



	}


	function init(){
		re.target = document.getElementById(dom_tgt);
		re.target.classList.add('res');
		re.trace_target = document.getElementById(trace_tgt);

		field_struct.map(f => {
			const res_node = document.createElement('div');
			res_node.classList.add('res-node');

			const el_label = document.createElement('div');
			el_label.classList.add('res-node-label');
			el_label.innerHTML = f.label
			const el = document.createElement(f.n);
			el.classList.add('res-node-field');
			el.setAttribute('id', f.id);

			set_field(el,`n/a`);

			res_node.appendChild(el_label);
			res_node.appendChild(el);

			re.target.appendChild(res_node);
			re.fields.push(el);

		})

		re.link_node = document.createElement('div');
		re.link_node.classList.add('res-link');
		re.link_node.innerHTML = 'link';
		re.link_node.style.display = 'none';
		re.target.parentNode.insertBefore(re.link_node, re.target);

		return re;
	}

	function json_cleaner(k, v){
		//#if(k === 'file') return `[data shortened (${v.length})chars]`;
		return v
	}

	function trace(t, reset){
		if(reset) re.trace_target.innerHTML = '';
		re.trace_target.innerHTML += `${t}<br>`;
	}

	const re = {
		link_field: null,
		fields:[],
		target: null,
		trace_target: null,
		init,
		trace,
		update,
		json_cleaner
	}

	return re

}

function server_callback(resource){
	for (let r of resource) {
		//console.log(r);
		RES.trace(`transaction completed with ${r.raw.status === 0 ? 'failure' : 'success'}`, true);
		RES.update(r.raw);
		if(r.acquire){
			if(r.raw.tx_token) resources.tx_token = r.raw.tx_token;
		}
		if(r.modify){
			if(r.raw.data) resources.data = r.raw.data;
		}
	}
}

function make_transaction(tx_result, next_objects){
	resources.tx_token = null;
	for (let r of tx_result) {
		if(r.raw.hasOwnProperty('tx_token')) resources.tx_token = r.raw.tx_token;
		RES.update(r.raw);
	}
	if(resources.tx_token !== null){
		RES.trace('token acquired, proceeding.');
		next_objects.map(obj => {
			obj.tx_token = resources.tx_token;
		})
		uiBasicLoader(next_objects).then(result => server_callback(result));
	}
}

function get_transaction(next_objects){
	RES.trace('acquiring token before proceeding.');
	const obj = [{url:'/acquire-transaction/', type:'json', acquire:true}]
	uiBasicLoader(obj).then(result => make_transaction(result, next_objects));
}

function validate_action(evt){
	const e = evt.target;

	if(e.dataset.ref === 'acquire'){
		RES.trace('testing acquire');
		const obj = [{url:'/acquire-transaction/', type:'json', acquire:true}]
		uiBasicLoader(obj).then(result => server_callback(result));
	}

	if(e.dataset.ref === 'modify'){
		RES.trace(`testing modify cmd:${e.dataset.cmd}`);
		let payload = null;
		let value = null;
		let path = null;

		if(e.dataset.cmd === 'expectations') {
			const input_data = JAM.get_text();
			if (input_data.length) {
				payload = Array.from(utf8Encode.encode(input_data));
			}
		}else if(e.dataset.cmd === 'put_file_path'){
			const input_data = JAM.get_text();
			path = document.querySelector('#path.res-node-field').value;

			if (input_data.length) {
				payload = Array.from(utf8Encode.encode(input_data));
			}
		}else if(e.dataset.cmd === 'get_file_path'){
			path = JAM.get_text();
		}

		const obj = [{
			url:'/admin/',
			type:'json',
			modify:true,
			tx_token:resources.tx_token,
			cmd:e.dataset.cmd,
			arg:{
				payload:payload,
				value:e.dataset.arg,
				path:path
			}

		}]
		get_transaction(obj);
	}

}

const elements = document.querySelectorAll('a[data-ref]');
for (let e of elements) {
	e.addEventListener('click', validate_action);
}

const JAM = eztext(document.getElementById('text-field')).init();
const RES = responder('tx-info', 'tx-trace').init();

document.addEventListener("DOMContentLoaded", () => {
  console.log("dom ready");
});
