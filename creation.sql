



create table if not exists movie
(
	"movieID" bigserial not null primary key,
	"title" varchar(120) not null,
	"watches" bigint not null,
	"releaseyear" int not null,
	"runtime" int not null
);

create table if not exists genre(
	"genreID" bigserial not null primary key,
	"name" varchar(30) not null
)

create table if not exists movie_genre
(
	"moviegenreID" bigserial not null primary key,
	"movieID" integer not null references movie("movieID") on update cascade on delete cascade,
	"genreID" integer not null references genre("genreID") on update cascade on delete cascade
);

create table if not exists movielist
(
	"movielistID" bigserial not null primary key,
	"title" varchar(120) not null,
	"url" varchar(120) not null
);

create table if not exists movie_movielist
(
	"moviemovielistID" bigserial not null primary key,
	"movieID" integer not null references movie("movieID") on update cascade on delete cascade,
	"movielistID" integer not null references movielist("movielistID") on update cascade on delete cascade
);
