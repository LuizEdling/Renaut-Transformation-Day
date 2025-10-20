<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('group_of_three', function (Blueprint $table) {
            $table->id();
            $table->integer('cube_1')->nullable();
            $table->integer('cube_2')->nullable();
            $table->integer('cube_3')->nullable();
            $table->float('group_time');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('group_of_three');
    }
};
