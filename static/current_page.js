function showSeletedTag() {
    const Tagvalue = localStorage.getItem('deviceTag');
    console.log(Tagvalue, 'hghgy')
    if (Tagvalue) {
        return Tagvalue
    }
    let elementVal = document.getElementById("samplePage");
    console.log(elementVal)
    elementVal.textContent =Tagvalue;

}
showSeletedTag();