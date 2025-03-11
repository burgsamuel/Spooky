//////////////////////////////////////////////////
// Setup Map
// ///////////////////////////////////////////////

const map = L.map("map").setView([-30.000, 135.0000], 4);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 20,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);



//////////////////////////////////////////////////
// Load user location
// ///////////////////////////////////////////////

function getLocation() {


  if (navigator.geolocation) {
    id = navigator.geolocation.getCurrentPosition(showPosition);
  } else {
    x.innerHTML = "Geolocation is not supported by this browser.";
  }
}

async function showPosition(position) {
  lat = position.coords.latitude;
  lon = position.coords.longitude;

  timeStamp = position.timestamp / 1000;

  map.flyTo(new L.LatLng(lat, lon), 15);


}



//////////////////////////////////////////////////
// Load points from server onto map for each user
// ///////////////////////////////////////////////



let totalSpotCounter = 0;


async function onload() {
  let response = await fetch("/mapData");
  let data = await response.json();


  let pixiContainer = new PIXI.Container();

  let pixiOverlay = L.pixiOverlay(function(utils) {
      let zoom = utils.getMap().getZoom();
      let container = utils.getContainer();
      let renderer = utils.getRenderer();
      let project = utils.latLngToLayerPoint;

      container.removeChildren();

      totalSpotCounter = data.length;
      updateSpotSpan();

      let baseSize = 2; 
      let zoomFactor = Math.pow(2, 13.2 - zoom); 
      let iconSize = baseSize * zoomFactor;

      // Add size limits
      let minSize = .1;
      let maxSize = 600; // adjusted max size
      iconSize = Math.max(minSize, Math.min(maxSize, iconSize));


      data.forEach(function(item) {
          if (item && typeof item.lat === 'number' && typeof item.lng === 'number' && item.iconUrl) {
              try {
                  let latlng = L.latLng(item.lat, item.lng);
                  let point = project(latlng);

                  PIXI.Texture.fromURL(item.iconUrl).then(texture => {
                      let sprite = new PIXI.Sprite(texture);

                      sprite.anchor.set(10 / 25, 10 / 25);
                      sprite.width = iconSize;
                      sprite.height = iconSize;

                      sprite.position.set(point.x, point.y);

                      container.addChild(sprite);
                      renderer.render(container);
                  }).catch(error => {
                      console.error("Error loading image:", item.iconUrl, error);
                  });
              } catch (error) {
                  console.error("Error processing item:", item, error);
              }
          } else {
              console.warn("Invalid data item:", item);
          }
      });

  }, pixiContainer).addTo(map);

  getLocation();
}

onload();



//////////////////////////////////////////////////
// load users spot count
// ///////////////////////////////////////////////

const spotCounterSpan = document.getElementById('spot-counter-span');

function updateSpotSpan(){

        spotCounterSpan.innerText = `Total Spots: ${totalSpotCounter}`;
  
  }
  
