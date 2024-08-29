// Gestion des champs d'article
document.addEventListener('DOMContentLoaded', function() {
    const addArticleButton = document.getElementById('add-article');
    const articlesContainer = document.getElementById('articles-container');

    addArticleButton.addEventListener('click', function() {
        // Créer un conteneur pour chaque nouvel article
        const newArticleGroup = document.createElement('div');
        newArticleGroup.className = 'article-group mb-2';

        newArticleGroup.innerHTML = `
            <input type="text" class="form-control mb-2" name="article_titres" placeholder="Titre de l'article" title="Titre de l'article" required>
            <textarea class="form-control mb-2" name="article_details" placeholder="Détails de l'article" required></textarea>
            <button type="button" class="btn btn-danger remove-article">Supprimer</button>
        `;

        articlesContainer.appendChild(newArticleGroup);

        // Ajouter l'événement pour supprimer l'article
        newArticleGroup.querySelector('.remove-article').addEventListener('click', function() {
            newArticleGroup.remove();
        });
    });
});
