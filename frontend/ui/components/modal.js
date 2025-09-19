const modalStyles = `
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(5px);
}
.modal-content {
    background-color: #2c2c2c;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    color: white;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    max-width: 85%;
    border: 1px solid #444;
}
.modal-content p {
    margin: 0;
    font-size: 1.1em;
}
.modal-close-btn {
    margin-top: 20px;
    padding: 10px 20px;
    border: none;
    background-color: #555;
    color: white;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
}
.modal-close-btn:hover {
    background-color: #666;
}
`;

const addModalStyles = () => {
    if (!document.getElementById('modal-styles')) {
        const styleSheet = document.createElement("style");
        styleSheet.id = 'modal-styles';
        styleSheet.type = "text/css";
        styleSheet.innerText = modalStyles;
        document.head.appendChild(styleSheet);
    }
};

export const showMessageModal = (message) => {
    addModalStyles();

    // Prevent creating multiple modals
    if (document.querySelector('.modal-overlay')) {
        return;
    }

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';

    const modal = document.createElement('div');
    modal.className = 'modal-content';

    const messageP = document.createElement('p');
    messageP.textContent = message;

    const closeButton = document.createElement('button');
    closeButton.textContent = 'OK';
    closeButton.className = 'modal-close-btn';

    const closeModal = () => {
        if (document.body.contains(overlay)) {
            document.body.removeChild(overlay);
        }
    };

    closeButton.onclick = closeModal;
    overlay.onclick = (e) => {
        if (e.target === overlay) {
            closeModal();
        }
    };

    modal.appendChild(messageP);
    modal.appendChild(closeButton);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
};
