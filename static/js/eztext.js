
export function eztext(dom_node){

    const check_line = () => Math.min(ez.max_lines, ez.num_lines);

    function set_text(txt){
        const n = `${txt}`.split('\n').length;
        ez.field.value = txt;
        ez.num_lines = n;
        ez.resize();
    }

    function get_text(){
        return ez.field.value;
    }

    function delta(evt){ //keyup
        evt.preventDefault(); // prevent usual browser behaviour
        const n = `${evt.target.value}`.split('\n').length;
        if(n !== ez.num_lines){
            ez.num_lines = n;
            ez.resize();
        }
    }

    function check_key(evt) { //keydown
        //# delete is 8
        //# return is 13
        //# tab is 9
        //#// this is black magic https://stackoverflow.com/questions/6637341/use-tab-to-indent-in-textarea
        if (evt.keyCode === 9) {
            evt.preventDefault(); // prevent usual browser behaviour
            let { value, selectionStart, selectionEnd } = ez.field;
            ez.field.value = value.slice(0, selectionStart) + "\t" + value.slice(selectionEnd);
            ez.field.setSelectionRange(selectionStart+2, selectionStart+2)
            console.log('tabbed');
        }

        if (evt.keyCode === 13) { // if the key code is 13 (ENTER)
            ez.num_lines ++;
            ez.resize();
        }
    }

    const l_n = (i) => {
        return {
            i:i,
            dom: document.createElement('div')
        }
    }

    function resize(){
        const ht = check_line(ez.num_lines) * ez.line_height + 'px';
        ez.numbers.style.height = ht;
        ez.field.style.height = ht;
        ez.dom_node.style.height = ht;

        for(let i = 0; i < ez.num_lines; i++){
            if(ez.line_numbers.list[i] === undefined){
                const l = l_n(i);
                const pre_text = `${i}`.padStart(2, '0')
                l.i = i;
                l.dom.textContent = pre_text;
                ez.line_numbers.list.push(i);
                ez.numbers.appendChild(l.dom);
            }
        }

        ez.line_numbers.list = ez.line_numbers.list.slice(0, ez.num_lines);
    }

    function init(){
        document.head.innerHTML += '<link rel="stylesheet" href="/css/eztext.css" type="text/css"/>';
        ez.dom_node.classList.add('ez_dom');

        ez.numbers = document.createElement('div');
        ez.numbers.classList.add('ez_numbers');
        ez.numbers.style.lineHeight = `${ez.line_height}px`;

        ez.field = document.createElement('textarea');
        ez.field.classList.add('ez_field');
        ez.field.setAttribute('placeholder','eztext');
        ez.field.setAttribute('rows','2');
        ez.field.style.lineHeight = `${ez.line_height}px`;

        ez.field.addEventListener('keyup', ez.delta);
        ez.field.addEventListener('keydown', ez.check_key);
        ez.field.addEventListener('scroll', function(){
            ez.numbers.scrollTo(0, this.scrollTop);
        });

        ez.dom_node.appendChild(ez.numbers);
        ez.dom_node.appendChild(ez.field);
        ez.resize();
        return ez;
    }

    const ez = {
        line_numbers: {list:[]},
        num_lines: 1,
        max_lines: 20,
        line_height: 16,
        dom_node: dom_node,
        field: null,
        numbers: null,
        set_text,
        get_text,
        init,
        delta,
        check_key,
        resize
    }

    return ez;
}
