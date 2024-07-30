// Gestion des champs de clause
document.addEventListener('DOMContentLoaded', function() {
    const addclauseButton = document.getElementById('add-clause');
    const clausesContainer = document.getElementById('clauses-container');

    addclauseButton.addEventListener('click', function() {
        const newclauseField = document.createElement('div');
        newclauseField.className = 'form-group';
        newclauseField.innerHTML = `
            <input type="text" class="form-control mb-2" name="clauses" placeholder="Veuillez saisir les clauses du contrat" title="Clauses" required>
            <button type="button" class="btn btn-danger remove-clause">Supprimer</button>
        `;
            clausesContainer.appendChild(newclauseField);
    
            newclauseField.querySelector('.remove-clause').addEventListener('click', function() {
                newclauseField.remove();
            });
        });
    });