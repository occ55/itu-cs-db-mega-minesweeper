CREATE TABLE chunks (
    competition_id integer NOT NULL,
    x integer NOT NULL,
    y integer NOT NULL,
    data character varying(255)[] NOT NULL
);



CREATE TABLE public.competitions (
    id integer NOT NULL,
    start bigint NOT NULL,
    "end" bigint NOT NULL,
    title character varying(255)[] NOT NULL,
    password character varying(255)[]
);


CREATE SEQUENCE public.competitions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.competitions_id_seq OWNED BY public.competitions.id;

CREATE TABLE public.event_log (
    id integer NOT NULL,
    user_id integer,
    competition_id integer,
    action text
);

CREATE SEQUENCE public.event_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.event_log_id_seq OWNED BY public.event_log.id;

CREATE TABLE public.flags (
    competition_id integer NOT NULL,
    chunk_x integer NOT NULL,
    chunk_y integer NOT NULL,
    offset_x integer NOT NULL,
    offset_y integer NOT NULL,
    user_id integer NOT NULL,
    state integer NOT NULL
);

CREATE TABLE public.guesses (
    competition_id integer NOT NULL,
    chunk_x integer NOT NULL,
    chunk_y integer NOT NULL,
    offset_x integer NOT NULL,
    offset_y integer NOT NULL,
    user_id integer NOT NULL
);

CREATE TABLE public.sessions (
    session_id character varying(255)[] NOT NULL,
    user_id integer NOT NULL
);

CREATE TABLE public.user_entries (
    user_id integer NOT NULL,
    competition_id integer NOT NULL,
    score integer DEFAULT 0 NOT NULL,
    join_time bigint NOT NULL,
    mines_hit integer DEFAULT 0 NOT NULL
);

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100)[] NOT NULL,
    password character varying(255)[] NOT NULL,
    elo integer DEFAULT 1000 NOT NULL
);

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;

ALTER TABLE ONLY public.competitions ALTER COLUMN id SET DEFAULT nextval('public.competitions_id_seq'::regclass);

ALTER TABLE ONLY public.event_log ALTER COLUMN id SET DEFAULT nextval('public.event_log_id_seq'::regclass);

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_pkey PRIMARY KEY (competition_id, x, y);

ALTER TABLE ONLY public.competitions
    ADD CONSTRAINT competitions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.event_log
    ADD CONSTRAINT event_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.flags
    ADD CONSTRAINT flags_pkey PRIMARY KEY (competition_id, chunk_x, chunk_y, offset_x, offset_y);

ALTER TABLE ONLY public.guesses
    ADD CONSTRAINT guesses_pkey PRIMARY KEY (competition_id, chunk_x, chunk_y, offset_x, offset_y);

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (session_id);

ALTER TABLE ONLY public.user_entries
    ADD CONSTRAINT user_entries_pkey PRIMARY KEY (user_id, competition_id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_entries
    ADD CONSTRAINT competitionid FOREIGN KEY (competition_id) REFERENCES public.competitions(id);

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT competitionid FOREIGN KEY (competition_id) REFERENCES public.competitions(id);

ALTER TABLE ONLY public.event_log
    ADD CONSTRAINT competitionid FOREIGN KEY (competition_id) REFERENCES public.competitions(id);

ALTER TABLE ONLY public.flags
    ADD CONSTRAINT competitionid FOREIGN KEY (competition_id) REFERENCES public.competitions(id);

ALTER TABLE ONLY public.guesses
    ADD CONSTRAINT competitionid FOREIGN KEY (competition_id) REFERENCES public.competitions(id);

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT userid FOREIGN KEY (user_id) REFERENCES public.users(id) NOT VALID;

ALTER TABLE ONLY public.user_entries
    ADD CONSTRAINT userid FOREIGN KEY (user_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.event_log
    ADD CONSTRAINT userid FOREIGN KEY (user_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.flags
    ADD CONSTRAINT userid FOREIGN KEY (user_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.guesses
    ADD CONSTRAINT userid FOREIGN KEY (user_id) REFERENCES public.users(id);

