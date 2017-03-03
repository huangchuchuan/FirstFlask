
window.addEventListener('load',function () {
    var form = {
        data:{
            nickname:'',
            password:''
        },
    };
    form.loginOwl = document.getElementById('login-owl');
    form.password = document.getElementById('password');
    form.nickname = document.getElementById('username');
    form.password.addEventListener('focus',function(){
        form.loginOwl.className = 'password';
    })
    form.password.addEventListener('blur',function(){
        form.loginOwl.className = '';
    })
})
