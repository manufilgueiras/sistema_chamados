document.addEventListener("DOMContentLoaded", function() {
    const formCadastro = document.getElementById("formCadastro");
    
    if (formCadastro) {
        formCadastro.addEventListener("submit", function(event) {
            const senha = document.getElementById("senhaCadastro").value;
            
            if (senha.length < 8) {
                alert("Menos de 8 caracteres? Essa senha aí até minha avó adivinha. Melhore isso se quiser se cadastrar! 🔐🙄");
                event.preventDefault();
            }
        });
    }
});