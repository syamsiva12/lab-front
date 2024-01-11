let selectedTag = "sssss";
function routeToPage(tag) { debugger
    selectedTag = tag;
//    routeToTagPage();
    localStorage.setItem('deviceTag', tag)
}

//handling route in js for now

function routeToTagPage(){
   const currentRoute=  window.location.href;
   const routeName = 'connect_page?';
   const path = currentRoute.concat(routeName);
   window.open(path);

}