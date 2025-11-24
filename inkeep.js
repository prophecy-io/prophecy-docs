function loadScript(url, callback) {
  const script = document.createElement('script');
  script.src = url;
  script.type = 'text/javascript';
  script.onload = callback;
  document.head.appendChild(script);
}

loadScript('https://cdn.jsdelivr.net/npm/@inkeep/cxkit-mintlify@0.5/dist/index.js', () => {
  const settings = {
    baseSettings: {
      apiKey: 'INKEEP_API_KEY', // required
      primaryBrandColor: '#403FC2', // required -- your brand color, the color scheme is derived from this
      organizationDisplayName: 'Prophecy',
      // ...optional settings
    },
    aiChatSettings: {
      // ...optional settings
      aiAssistantAvatar: '/images/icon.png',
      exampleQuestions: [
        'Do I need a fabric to run my pipeline?',
        'How can Copilot help me build projects?',
        'How do I add data to my pipeline?',
        'Can I monitor my deployed projects?',
      ],
    },
  };

  // Initialize the UI components
  Inkeep.ModalSearchAndChat(settings); // Search Bar
  Inkeep.ChatButton(settings); // 'Ask AI' button
});
