function loadScript(url, callback, type = 'module') {
  const script = document.createElement('script');
  script.src = url;
  script.type = type;
  script.onload = callback;
  document.head.appendChild(script);
}

// Shared settings configuration
const styleOverrides = `
  .ikp-sidebar-chat__root {
    @media (max-width: 576px) {
      --width: 100% !important;
    }
  }
`;

const baseSettings = {
  baseSettings: {
    apiKey: '1ad64cdd8b65ffda750f6158e356585bf684dba789a84432', // required
    primaryBrandColor: '#403fc2', // required -- your brand color, the color scheme is derived from this
    organizationDisplayName: 'Prophecy',
    theme: {
      styles: [
        {
          key: 'inkeep-style-overrides',
          type: 'style',
          value: styleOverrides,
        },
      ],
    },
  },
};

// Load the original script for SidebarChat functionality
loadScript('https://cdn.jsdelivr.net/npm/@inkeep/cxkit-js@0.5/dist/embed.js', () => {
  const sidebarSettings = {
    ...baseSettings,
    isOpen: false,
    onOpenChange: (isOpen) => {
      if (widget) {
        widget.update({ isOpen: isOpen });
      }
    },
    minWidth: 368,
    maxWidth: 576,
  };

  // Creates the target div for the sidebar
  const sidebarTarget = document.createElement('div');
  sidebarTarget.id = 'inkeep-sidebar';
  sidebarTarget.style.position = 'fixed';
  sidebarTarget.style.top = '0';
  sidebarTarget.style.right = '0';
  sidebarTarget.style.height = '100%';
  sidebarTarget.style.backgroundColor = 'white';
  sidebarTarget.style.zIndex = '1000';
  document.body.appendChild(sidebarTarget);

  // Add sibling button to search bar
  function addSiblingButton() {
    const searchBar = document.getElementById('search-bar-entry');

    if (searchBar) {
      // Create the new button with similar styling
      const newButton = document.createElement('button');
      newButton.type = 'button';
      newButton.className =
        'flex shrink-0 pointer-events-auto rounded-2xl items-center text-sm leading-6 h-9 px-3 text-gray-500 dark:text-white/50 bg-background-light dark:bg-background-dark dark:brightness-[1.1] dark:ring-1 dark:hover:brightness-[1.25] ring-1 ring-gray-400/30 hover:ring-gray-600/30 dark:ring-gray-600/30 dark:hover:ring-gray-500/30 justify-between truncate gap-2 ml-2';
      newButton.setAttribute('aria-label', 'Ask AI');

      // Add content to the button
      newButton.innerHTML = `
        <div class="flex items-center gap-2 min-w-[42px]">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkles min-w-4 flex-none text-gray-700 hover:text-gray-800 dark:text-gray-400 hover:dark:text-gray-200">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path>
            <path d="M5 3v4"></path>
            <path d="M19 17v4"></path>
            <path d="M3 5h4"></path>
            <path d="M17 19h4"></path>
          </svg>
          <div class="truncate min-w-0">Ask AI</div>
        </div>
      `;

      // Add click handler to trigger the sidebar
      newButton.addEventListener('click', () => {
        if (widget) {
          widget.update({ isOpen: true });
        }
      });

      // Insert the button after the search bar
      searchBar.parentNode.insertBefore(newButton, searchBar.nextSibling);
    } else {
      console.warn('Search bar not found');
    }
  }

  // Call the function when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addSiblingButton);
  } else {
    addSiblingButton();
  }

  // Initialize the SidebarChat widget
  const widget = Inkeep.SidebarChat('#inkeep-sidebar', sidebarSettings);

  // Load the Mintlify script for ModalSearchAndChat
  loadScript(
    'https://cdn.jsdelivr.net/npm/@inkeep/cxkit-mintlify@0.5/dist/index.js',
    () => {
      // Initialize ModalSearchAndChat component
      Inkeep.ModalSearchAndChat(baseSettings);
    },
    'text/javascript'
  );
});
