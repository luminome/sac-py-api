//import data_store from "./static/data/data-store.json"

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
const page_output = document.getElementById('output');
const utf8Encode = new TextEncoder();
const utf8Decode = new TextDecoder();


function decode_uint_array(el){
	const ref = Object.entries(el).map(e=> e[1]);
	const ref_arr = new Uint8Array(ref);
	console.log(ref_arr);
	return utf8Decode.decode(ref_arr);
}


const loaded_assets = {};


function loaded_sources(resource){
	for(let r of resource){

		if(r.raw.hasOwnProperty('error')){
			alert(r.raw.error);
			continue;
		}

		if(r.type === 'md'){
			loaded_assets[r.name] = r.raw;
			const output = document.createElement('div');
			output.classList.add('row');
			output.innerHTML = r.raw;
			page_output.appendChild(output);
		}

		const data = r.raw;

		if(r.type === 'json') {
			Object.entries(data.result).map(d => {
				console.log(d);
				if (d[1] !== null) {
					const output = document.createElement('div');
					output.classList.add('row');
					Object.entries(d[1]).map(s_d => {
						//if(s_d[0] === 'b')
						const s_output = document.createElement('div');
						s_output.classList.add('column');
						s_output.innerHTML = s_d[0] === 'b' ? decode_uint_array(s_d[1]) : s_d[1];
						output.appendChild(s_output);
					})

					page_output.appendChild(output);
				}
			})
		}

		const output = document.createElement('div');
		output.innerHTML = `${data.time}`;
		page_output.appendChild(output);
		//output.classList.add('row');
		//output.textContent = JSON.stringify(data, null, 2);


	}
}



//
// // const obj = [
// // 	{url:'http://localhost:5000/sources', type:'json'},
// // 	{url:'http://localhost:5000/data_store', type:'json'},
// // 	{url:'http://localhost:5000/io', type:'json', post:true}]
//
// let fpt = 'this is my severly borked\"and ecsaped thing with <> and #$%^&*(';
//
// console.log(utf8Encode.encode(fpt));
//
// const obj = [
// 	// {name:'md_file', url:'https://luminome.com/static/sources/sac-py-api.md', type:'md'},
// 	// {url:'https://luminome.com/data_store', type:'json'},
// 	{url:'http://localhost:5000/api/token/', type:'json', post:true, b:utf8Encode.encode(fpt)}]
//
//
// //
// // uiBasicLoader(obj).then(result => loaded_sources(result));
//
// const validated = {'state':null, 'kw':null};
//
//
// function validation_process(resource) {
// 	for (let r of resource) {
// 		console.log(r.raw);
// 		if(r.raw.hasOwnProperty('username')){
// 			validated.state = 'user_set';
// 		}
// 		if(r.raw.hasOwnProperty('token')){
// 			validated.state = 'token_set';
// 			validated.token = r.raw.token;
// 			console.log('token saved', validated);
// 		}
// 	}
// }
//
//
// //phase one: create a user
// const kw = document.getElementById('kw');
// kw.addEventListener('change', validate);
//
// // const pw = document.getElementById('pw');
// // pw.addEventListener('change', validate);
//
// const tst = document.getElementById('trigger');
// tst.addEventListener('click', validate);
//
// const message = document.getElementById('message');
//
// function recall(resource){
// 	for (let r of resource) {
// 		console.log(r);
// 		if(r.raw.hasOwnProperty('error')) message.innerHTML = r.raw.error;
// 		//if(r.raw.hasOwnProperty('tx_token')) validated.kw = r.raw.tx_token;
// 		kw.value = validated.kw;
// 	}
// }
//
// function validate(evt){
//
// 	validated[evt.target.id] = evt.target.value;
//
// 	if(kw.value) validated['kw'] = kw.value;
//
// 	console.log(validated);
//
// 	if(validated.hasOwnProperty('kw')) {
// 		const obj = [{url:'http://localhost:5000/admin/', v:validated, type:'json', test:true, b:utf8Encode.encode(fpt)}]
// 		uiBasicLoader(obj).then(result => recall(result));
// 	}
// }

// console.log(document.querySelectorAll('a[data-ref]'));
// console.log(Base64.encode('okay'));

const resources = {}
const server_result = document.getElementById('result');

function server_callback(resource){
	for (let r of resource) {
		console.log(r);

		const ref = Object.entries(r.raw).map((r,n)=> {
			return `${n} ${r[0]}: ${r[1]}`
		});
		
		server_result.innerHTML += ref.join('</br>')+'</br>';

		if(r.acquire){
			if(r.raw.hasOwnProperty('tx_token')) resources.tx_token = r.raw.tx_token;
		}

		if(r.modify){
			if(r.raw.hasOwnProperty('data')) resources.data = r.raw.data;
		}

		console.log(resources);
	}
}

function loaded_resources(resource) {
	for (let r of resource) {

		resources[r.name] = r.raw;
		console.log(resources);
	}
}




function validate_action(evt){
	const e = evt.target;

	if(e.dataset.ref === 'acquire'){
		console.log('testing acquire');
		const obj = [{url:'/acquire-transaction/', type:'json', acquire:true}]
		uiBasicLoader(obj).then(result => server_callback(result));
	}

	if(e.dataset.ref === 'modify'){
		console.log('testing modify');
		//const payload = e.dataset.cmd ? e.dataset.cmd : Array.from(utf8Encode.encode(resources['md_file']));
		let payload = null;

		if(e.dataset.cmd === 'expectations'){
			const input_data = document.getElementById('pre-data');
			if(input_data.value.length){
				payload = Array.from(utf8Encode.encode(input_data.value));
			}
		}else{
			payload = e.dataset.cmd;
		}


		const obj = [{url:'/admin/', type:'json', modify:true, cmd:e.dataset.cmd, arg:e.dataset.arg, tx_token:resources.tx_token, b:payload}]
		uiBasicLoader(obj).then(result => server_callback(result));
	}

}

const elements = document.querySelectorAll('a[data-ref]');
for (let e of elements) {
	e.addEventListener('click', validate_action);
}


const obj = [{name:'md_file', url:'https://luminome.com/static/sources/sac-py-api.md', type:'md'}]
uiBasicLoader(obj).then(result => loaded_resources(result));


//
// uiBasicLoader(obj).then(result => loaded_sources(result));
