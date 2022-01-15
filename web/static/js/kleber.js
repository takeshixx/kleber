function create_paste() {
    var encrypt = document.getElementById('id_is_encrypted');
    var secure_shortcut = document.getElementById('id_secure_shortcut');
    var paste_content = document.getElementById('id_content').value;
    var paste_name = document.getElementById('id_name').value;
    var paste_lifetime = document.getElementById('id_lifetime').value;
    var csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    if(!encrypt.checked || paste_content == '')
        return true;
    var random_key = sjcl.random.randomWords(4);
    var encryption_key = sjcl.codec.hex.fromBits(random_key);
    var encrypted_content = sjcl.encrypt(encryption_key, paste_content);
    if (!csrfmiddlewaretoken) {
        alert('Could not read csrfmiddlewaretoken');
        return false;
    }
    var post_data = '{"content": "' + encodeURIComponent(encrypted_content) + '", ' +
                    '"name": "' + paste_name + '", ' +
                    '"lifetime": ' + paste_lifetime + ', ' +
                    '"secure_shortcut": ' + secure_shortcut.checked + ',' +
                    '"is_encrypted": true}';
    var fetch_headers = new Headers();
    fetch_headers.append('Content-Type', 'application/json; charset=UTF-8');
    fetch_headers.append('X-CSRFTOKEN', csrfmiddlewaretoken);
    var fetch_init = {method: 'POST',
                      headers: fetch_headers,
                      body: post_data,
                      credentials: 'include'};
    var fetch_req = new Request(window.location.origin + '/api/pastes/', fetch_init);
    fetch(fetch_req)
        .then(function (response) {
            var contentType = response.headers.get("content-type");
            if(contentType && contentType.indexOf("application/json") !== -1 && response.ok) {
                return response.json();
            } else {
                alert('Invalid response');
                return false;
            }
        })
        .then(function (json) {
            if(json.shortcut){
                window.location = window.location.origin + '/' + json.shortcut + '#' + encryption_key;
            } else {
                alert('shortcut not set');
                return false;
            }
        })
        .catch(function (error) {
            alert(error);
        });
    return false;
}
function protect() {
    var random_bytes = sjcl.random.randomWords(4);
    var random_password = sjcl.codec.hex.fromBits(random_bytes);
    var password = document.getElementById('id_password');
    password.value = random_password;
    password.classList.toggle('hidden');
}
