// React is globally available in Mintlify, no import needed
export const WistiaVideo = ({ mediaId, autoplay = true, muted = true, loop = true }) => {
  const containerRef = React.useRef(null);
  const playerRef = React.useRef(null);
  const wistiaPlayerRef = React.useRef(null);

  const initWistia = () => {
    if (!containerRef.current || playerRef.current) return;

    const container = containerRef.current;
    const playerId = `wistia_${mediaId}_${Math.random().toString(36).substr(2, 9)}`;

    // Create the embed div
    container.innerHTML = '';
    const embedDiv = document.createElement('div');
    embedDiv.className = `wistia_embed wistia_async_${mediaId}`;
    embedDiv.id = playerId;
    container.appendChild(embedDiv);

    // Initialize Wistia player
    if (window._wq) {
      window._wq.push({
        id: playerId,
        onReady: (video) => {
          wistiaPlayerRef.current = video;
          // Set loop after player is ready
          if (loop) {
            video.bind('end', () => {
              video.play();
            });
          }
        },
        options: {
          autoPlay: autoplay,
          muted: muted,
          videoFoam: true,
        },
      });
    }

    playerRef.current = playerId;
  };

  React.useEffect(() => {
    // Check if Wistia script is already loaded
    if (window._wq) {
      initWistia();
      return;
    }

    // Load Wistia embed script
    const script = document.createElement('script');
    script.src = 'https://fast.wistia.com/assets/external/E-v1.js';
    script.async = true;
    script.onload = () => {
      window._wq = window._wq || [];
      initWistia();
      window.dispatchEvent(new Event('wistia-loaded'));
    };
    document.head.appendChild(script);

    // Also listen for the event in case script was loaded elsewhere
    const checkWistia = () => {
      if (window._wq) {
        initWistia();
        window.removeEventListener('wistia-loaded', checkWistia);
      }
    };
    window.addEventListener('wistia-loaded', checkWistia);

    return () => {
      window.removeEventListener('wistia-loaded', checkWistia);
      // Cleanup player if needed
      if (playerRef.current && window.Wistia && window.Wistia.api) {
        const player = window.Wistia.api(playerRef.current);
        if (player) {
          player.remove();
        }
      }
    };
  }, [mediaId, autoplay, muted, loop]);

  return (
    <div
      ref={containerRef}
      className="aspect-video w-full rounded-xl"
      style={{ position: 'relative' }}
    />
  );
};
