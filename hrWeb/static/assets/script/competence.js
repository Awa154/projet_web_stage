// Gestion des champs de compétence
document.addEventListener('DOMContentLoaded', function() {
    const addCompetenceButton = document.getElementById('add-competence');
    const competencesContainer = document.getElementById('competences-container');

    addCompetenceButton.addEventListener('click', function() {
        // Créer un conteneur pour chaque nouveau champ de compétence
        const newCompetenceRow = document.createElement('div');
        newCompetenceRow.className = 'row mb-2';

        newCompetenceRow.innerHTML = `
            <div class="col-sm-6 col-12">
                <input type="text" class="form-control" name="competences" placeholder="Compétence" title="Compétence" required>
            </div>
            <div class="col-sm-6 col-12">
                <button type="button" class="btn btn-danger remove-competence">Supprimer</button>
            </div>
        `;

        competencesContainer.appendChild(newCompetenceRow);

        // Ajouter l'événement pour supprimer le champ
        newCompetenceRow.querySelector('.remove-competence').addEventListener('click', function() {
            newCompetenceRow.remove();
        });
    });
});




    



    