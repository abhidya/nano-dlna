            
              
                var canvas, c, w, h, twoPI = Math.PI * 2, pipes = new Array();
$(document).ready(function(){
  canvas = document.getElementById("canvas");
  c = canvas.getContext("2d");
  w = canvas.width;
  h = canvas.height;
  
  var pipe = function(colour){
    this.rad = 5;
    this.maxRad = 30;
    this.fill = null;
    this.colour = colour;
    this.position = { x: 0, y: 0 };
    this.target = { x: 0, y: 0 };
    this.direction = {x: 1, y: 0};
    this.speed = 1;
    this.create = function(){
      this.rad = 5;
      this.position.x = Math.random()*w |0;
      this.position.y = Math.random()*h |0;
      do {
        this.target.x = this.position.x + ((Math.random()*200)-100) |0;
      } while( this.target.x < this.rad || this.target.x > w-this.rad );
      this.target.y = this.position.y;
      this.direction.x = (this.position.x > this.target.x) ? -1 : 1;
      this.direction.y = 0;
      this.colour.a = 0;
    };
    this.move = function(){
      this.position.x += this.direction.x;
      this.position.y += this.direction.y;
      if( (this.direction.x > 0 && this.position.x > this.target.x) || (this.direction.x < 0 && this.position.x < this.target.x) ){
        this.target.x = this.position.x;
        do {
          this.target.y = this.position.y + (Math.random()*200)-100 |0;
        } while( this.target.y < this.rad || this.target.y > h-this.rad );
        this.direction.x = 0;
        this.direction.y = this.position.y > this.target.y ? -1 : 1;
      }
      if( (this.direction.y > 0 && this.position.y > this.target.y) || (this.direction.y < 0 && this.position.y < this.target.y) ){
        this.target.y = this.position.y;
        do {
          this.target.x = this.position.x + ((Math.random()*200)-100) |0;
        } while( this.target.x < this.rad || this.target.x > w-this.rad );
        this.direction.y = 0;
        this.direction.x = this.position.x > this.target.x ? -1 : 1;
      }
      this.rad += 0.005;
      if(this.rad > this.maxRad){
        this.create();
        c.clear();
      }
      if(this.colour.a < 1) this.colour.a += 0.005;
      
      this.draw();
    };
    this.draw = function(){
      this.setFill();
      c.fillStyle = this.fill;
      c.beginPath();
      c.arc(this.position.x, this.position.y, this.rad, 0, twoPI, true);
      c.closePath();
      c.fill();
      
      c.save();
      c.fillStyle = "rgba(0,0,0,0.75)";
      c.beginPath();
      c.arc(this.position.x, this.position.y, this.rad-2, 0, twoPI, true);
  		c.closePath();
      c.fill();
      c.restore();
    };
    this.setFill = function(){
      this.fill = c.createLinearGradient(this.position.x-(this.rad/2),this.position.y-(this.rad/2),this.position.x+(this.rad/2),this.position.y+(this.rad/2));
      this.fill.addColorStop(0, "rgba("+this.colour.r+","+this.colour.g+","+this.colour.b+","+this.colour.a+")");
      this.fill.addColorStop(1, "rgba("+(this.colour.r/100*20|0)+","+(this.colour.g/100*20|0)+","+(this.colour.b/100*20|0)+","+this.colour.a+")");
    };
    this.create();
  };
  
  var animate = function(){
    for( p in pipes ){
      pipes[p].move();
    }
  };
  
  pipes.push(new pipe( {r:105, g:210, b:231} ));
  pipes.push(new pipe( {r:167, g:219, b:219} ));
  pipes.push(new pipe( {r:224, g:228, b:204} ));
  pipes.push(new pipe( {r:243, g:134, b:48 } ));
  pipes.push(new pipe( {r:250, g:105, b:0  } ));
  
  var gTimer = window.setInterval(animate,10);
  
  CanvasRenderingContext2D.prototype.clear = function(preserve){
    this.save();
    this.clearRect(0,0,this.canvas.width,this.canvas.height);
    this.restore();
  };
});
              
