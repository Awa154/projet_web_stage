// Gestion des champs de compétence
document.addEventListener('DOMContentLoaded', function() {
    const addCompetenceButton = document.getElementById('add-competence');
    const competencesContainer = document.getElementById('competences-container');

    addCompetenceButton.addEventListener('click', function() {
        const newCompetenceField = document.createElement('div');
        newCompetenceField.className = 'form-group';
        newCompetenceField.innerHTML = `
            <input type="text" class="form-control mb-2" name="competences" placeholder="Compétence" title="Compétence" required>
            <button type="button" class="btn btn-danger remove-competence">Supprimer</button>
        `;
            competencesContainer.appendChild(newCompetenceField);
    
            newCompetenceField.querySelector('.remove-competence').addEventListener('click', function() {
                newCompetenceField.remove();
            });
        });
    });



    