--
-- PostgreSQL database dump
--

\restrict jR3x84203W3g4qHZvna2Iw2od2KHhFKR6UxO1F6YcqgG5DNiwcU4MaJS9uF5rLc

-- Dumped from database version 12.22 (Debian 12.22-1.pgdg120+1)
-- Dumped by pg_dump version 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: schema_update_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_update_history (
    version_partition integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    update_time timestamp without time zone NOT NULL,
    description character varying(255),
    manifest_md5 character varying(64),
    new_version character varying(64),
    old_version character varying(64)
);


--
-- Name: schema_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_version (
    version_partition integer NOT NULL,
    db_name character varying(255) NOT NULL,
    creation_time timestamp without time zone,
    curr_version character varying(64),
    min_compatible_version character varying(64)
);


--
-- Name: schema_update_history schema_update_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_update_history
    ADD CONSTRAINT schema_update_history_pkey PRIMARY KEY (version_partition, year, month, update_time);


--
-- Name: schema_version schema_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_version
    ADD CONSTRAINT schema_version_pkey PRIMARY KEY (version_partition, db_name);


--
-- PostgreSQL database dump complete
--

\unrestrict jR3x84203W3g4qHZvna2Iw2od2KHhFKR6UxO1F6YcqgG5DNiwcU4MaJS9uF5rLc

